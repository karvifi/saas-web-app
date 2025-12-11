"""
Background job processing for AI Agent Platform
Handles long-running tasks, scheduled jobs, and task queues
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import uuid
import os
from pathlib import Path
import redis
from dataclasses import dataclass, asdict
import pickle

logger = logging.getLogger(__name__)

@dataclass
class Job:
    """Job data structure"""
    job_id: str
    job_type: str
    payload: Dict[str, Any]
    priority: int = 1  # 1=low, 2=normal, 3=high, 4=critical
    status: str = "queued"  # queued, running, completed, failed, cancelled
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    user_id: Optional[str] = None
    timeout: int = 3600  # seconds

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class JobQueue:
    """Redis-based job queue system"""

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379,
                 redis_db: int = 0, redis_password: Optional[str] = None):
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=False  # We need binary for pickle
        )

        # Queue names
        self.queues = {
            1: "ai_agent:jobs:low",
            2: "ai_agent:jobs:normal",
            3: "ai_agent:jobs:high",
            4: "ai_agent:jobs:critical"
        }

        self.job_data_key = "ai_agent:job_data"
        self.processing_key = "ai_agent:jobs:processing"

        # Test connection
        try:
            self.redis.ping()
            logger.info("Job queue Redis connection established")
        except redis.ConnectionError:
            logger.warning("Job queue Redis connection failed - using fallback mode")
            self.redis = None

    def _serialize_job(self, job: Job) -> bytes:
        """Serialize job for storage"""
        return pickle.dumps(job)

    def _deserialize_job(self, data: bytes) -> Job:
        """Deserialize job from storage"""
        return pickle.loads(data)

    async def enqueue_job(self, job_type: str, payload: Dict[str, Any],
                         priority: int = 2, user_id: Optional[str] = None,
                         timeout: int = 3600, max_retries: int = 3) -> str:
        """Add job to queue"""
        if not self.redis:
            logger.warning("Redis not available - job not queued")
            return None

        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type=job_type,
            payload=payload,
            priority=priority,
            user_id=user_id,
            timeout=timeout,
            max_retries=max_retries
        )

        try:
            # Store job data
            job_key = f"{self.job_data_key}:{job_id}"
            self.redis.set(job_key, self._serialize_job(job))

            # Add to appropriate queue
            queue_name = self.queues.get(priority, self.queues[2])
            self.redis.lpush(queue_name, job_id)

            logger.info(f"Job {job_id} ({job_type}) queued with priority {priority}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return None

    async def dequeue_job(self, priority: int = 2) -> Optional[Job]:
        """Get next job from queue"""
        if not self.redis:
            return None

        # Try higher priority queues first
        for p in range(4, 0, -1):
            if p < priority:
                continue

            queue_name = self.queues[p]
            try:
                # Use BRPOP to block and wait for job
                result = self.redis.brpop(queue_name, timeout=1)
                if result:
                    job_id = result[1].decode('utf-8')
                    job_key = f"{self.job_data_key}:{job_id}"

                    job_data = self.redis.get(job_key)
                    if job_data:
                        job = self._deserialize_job(job_data)
                        job.status = "running"
                        job.started_at = datetime.utcnow()

                        # Mark as processing
                        self.redis.sadd(self.processing_key, job_id)

                        # Update job data
                        self.redis.set(job_key, self._serialize_job(job))

                        logger.info(f"Job {job_id} dequeued and started")
                        return job

            except Exception as e:
                logger.error(f"Error dequeuing job from priority {p}: {e}")
                continue

        return None

    async def complete_job(self, job_id: str, result: Any = None):
        """Mark job as completed"""
        if not self.redis:
            return

        try:
            job_key = f"{self.job_data_key}:{job_id}"
            job_data = self.redis.get(job_key)

            if job_data:
                job = self._deserialize_job(job_data)
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.result = result

                # Remove from processing set
                self.redis.srem(self.processing_key, job_id)

                # Update job data
                self.redis.set(job_key, self._serialize_job(job))

                logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Failed to complete job {job_id}: {e}")

    async def fail_job(self, job_id: str, error: str):
        """Mark job as failed"""
        if not self.redis:
            return

        try:
            job_key = f"{self.job_data_key}:{job_id}"
            job_data = self.redis.get(job_key)

            if job_data:
                job = self._deserialize_job(job_data)
                job.status = "failed"
                job.error = error
                job.completed_at = datetime.utcnow()

                # Remove from processing set
                self.redis.srem(self.processing_key, job_id)

                # Check if we should retry
                if job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = "queued"
                    job.error = None
                    job.completed_at = None
                    job.started_at = None

                    # Re-queue the job
                    queue_name = self.queues.get(job.priority, self.queues[2])
                    self.redis.lpush(queue_name, job_id)

                    logger.info(f"Job {job_id} failed, retrying ({job.retry_count}/{job.max_retries})")
                else:
                    logger.error(f"Job {job_id} failed permanently: {error}")

                # Update job data
                self.redis.set(job_key, self._serialize_job(job))

        except Exception as e:
            logger.error(f"Failed to fail job {job_id}: {e}")

    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get job status"""
        if not self.redis:
            return None

        try:
            job_key = f"{self.job_data_key}:{job_id}"
            job_data = self.redis.get(job_key)

            if job_data:
                return self._deserialize_job(job_data)

        except Exception as e:
            logger.error(f"Failed to get job status {job_id}: {e}")

        return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job"""
        if not self.redis:
            return False

        try:
            job_key = f"{self.job_data_key}:{job_id}"
            job_data = self.redis.get(job_key)

            if job_data:
                job = self._deserialize_job(job_data)
                if job.status == "queued":
                    job.status = "cancelled"
                    job.completed_at = datetime.utcnow()

                    # Remove from processing set if it's there
                    self.redis.srem(self.processing_key, job_id)

                    # Update job data
                    self.redis.set(job_key, self._serialize_job(job))

                    logger.info(f"Job {job_id} cancelled")
                    return True

        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")

        return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        if not self.redis:
            return {"status": "disconnected"}

        try:
            stats = {
                "status": "connected",
                "queues": {},
                "processing": self.redis.scard(self.processing_key),
                "total_jobs": 0
            }

            for priority, queue_name in self.queues.items():
                queue_length = self.redis.llen(queue_name)
                stats["queues"][f"priority_{priority}"] = queue_length
                stats["total_jobs"] += queue_length

            return stats

        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"status": "error", "error": str(e)}

class JobProcessor:
    """Job processor that handles job execution"""

    def __init__(self, job_queue: JobQueue):
        self.job_queue = job_queue
        self.job_handlers: Dict[str, Callable] = {}
        self.running = False

    def register_handler(self, job_type: str, handler: Callable):
        """Register a job handler function"""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    async def process_jobs(self, max_concurrent: int = 5):
        """Main job processing loop"""
        self.running = True
        logger.info("Job processor started")

        semaphore = asyncio.Semaphore(max_concurrent)

        try:
            while self.running:
                # Get next job
                job = await self.job_queue.dequeue_job()

                if job:
                    # Process job with concurrency control
                    asyncio.create_task(self._process_job_with_semaphore(job, semaphore))
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Job processor error: {e}")
        finally:
            self.running = False
            logger.info("Job processor stopped")

    async def _process_job_with_semaphore(self, job: Job, semaphore: asyncio.Semaphore):
        """Process a job with semaphore control"""
        async with semaphore:
            await self._process_job(job)

    async def _process_job(self, job: Job):
        """Process a single job"""
        try:
            logger.info(f"Processing job {job.job_id} ({job.job_type})")

            # Get handler
            handler = self.job_handlers.get(job.job_type)
            if not handler:
                raise ValueError(f"No handler registered for job type: {job.job_type}")

            # Execute job with timeout
            result = await asyncio.wait_for(
                handler(job.payload, job.user_id),
                timeout=job.timeout
            )

            # Mark as completed
            await self.job_queue.complete_job(job.job_id, result)

        except asyncio.TimeoutError:
            error = f"Job timed out after {job.timeout} seconds"
            logger.error(f"Job {job.job_id} timeout: {error}")
            await self.job_queue.fail_job(job.job_id, error)

        except Exception as e:
            error = str(e)
            logger.error(f"Job {job.job_id} failed: {error}")
            await self.job_queue.fail_job(job.job_id, error)

    async def stop(self):
        """Stop the job processor"""
        self.running = False
        logger.info("Job processor stopping...")

# Global instances
job_queue = JobQueue()
job_processor = JobProcessor(job_queue)

# Built-in job handlers
async def handle_task_execution(payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Handle AI agent task execution"""
    # This would integrate with your existing agent system
    agent_name = payload.get("agent")
    task_data = payload.get("task_data", {})

    # Simulate task execution (replace with actual agent calls)
    await asyncio.sleep(2)  # Simulate processing time

    result = {
        "agent": agent_name,
        "task": task_data,
        "status": "completed",
        "result": f"Task executed by {agent_name}",
        "timestamp": datetime.utcnow().isoformat()
    }

    return result

async def handle_data_processing(payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Handle data processing jobs"""
    operation = payload.get("operation")
    data = payload.get("data", [])

    # Simulate data processing
    await asyncio.sleep(1)

    result = {
        "operation": operation,
        "processed_items": len(data),
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat()
    }

    return result

async def handle_notification(payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Handle notification sending jobs"""
    notification_type = payload.get("type")
    recipients = payload.get("recipients", [])

    # Simulate notification sending
    await asyncio.sleep(0.5)

    result = {
        "type": notification_type,
        "recipients_count": len(recipients),
        "status": "sent",
        "timestamp": datetime.utcnow().isoformat()
    }

    return result

async def handle_backup(payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Handle backup operations"""
    backup_type = payload.get("type", "full")
    target = payload.get("target")

    # Simulate backup process
    await asyncio.sleep(5)

    result = {
        "backup_type": backup_type,
        "target": target,
        "status": "completed",
        "size_mb": 150.5,
        "timestamp": datetime.utcnow().isoformat()
    }

    return result

# Register built-in handlers
job_processor.register_handler("task_execution", handle_task_execution)
job_processor.register_handler("data_processing", handle_data_processing)
job_processor.register_handler("notification", handle_notification)
job_processor.register_handler("backup", handle_backup)

# Helper functions
async def enqueue_task_execution(agent: str, task_data: Dict[str, Any],
                               user_id: str, priority: int = 2) -> Optional[str]:
    """Enqueue an AI agent task for execution"""
    payload = {
        "agent": agent,
        "task_data": task_data
    }

    return await job_queue.enqueue_job(
        "task_execution", payload,
        priority=priority, user_id=user_id
    )

async def enqueue_data_processing(operation: str, data: List[Any],
                                user_id: Optional[str] = None, priority: int = 1) -> Optional[str]:
    """Enqueue a data processing job"""
    payload = {
        "operation": operation,
        "data": data
    }

    return await job_queue.enqueue_job(
        "data_processing", payload,
        priority=priority, user_id=user_id
    )

async def enqueue_notification(notification_type: str, recipients: List[str],
                             priority: int = 2) -> Optional[str]:
    """Enqueue a notification job"""
    payload = {
        "type": notification_type,
        "recipients": recipients
    }

    return await job_queue.enqueue_job(
        "notification", payload,
        priority=priority
    )

async def enqueue_backup(backup_type: str = "full", target: str = "database",
                        priority: int = 1) -> Optional[str]:
    """Enqueue a backup job"""
    payload = {
        "type": backup_type,
        "target": target
    }

    return await job_queue.enqueue_job(
        "backup", payload,
        priority=priority
    )

async def start_job_processor(max_concurrent: int = 5):
    """Start the background job processor"""
    await job_processor.process_jobs(max_concurrent)

async def stop_job_processor():
    """Stop the background job processor"""
    await job_processor.stop()