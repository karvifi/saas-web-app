"""
Monitoring and Analytics System
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import os
from loguru import logger
# from backend.user_profiles import UserProfileManager


class MonitoringSystem:
    """
    System for monitoring agent performance and user analytics
    """

    def __init__(self, profile_manager=None):
        self.metrics_file = "data/metrics.json"
        os.makedirs("data", exist_ok=True)
        # self.profile_manager = profile_manager or UserProfileManager()

    def record_task_execution(self, task_id: str, user_id: str, agent_type: str,
                            query: str, execution_time: float, success: bool,
                            result_summary: str = ""):
        """Record task execution metrics"""
        try:
            # Save to database
            self.profile_manager.log_task_execution(
                user_id, agent_type, query, agent_type, success, execution_time,
                None if success else result_summary
            )

            # Also save to JSON for backward compatibility
            metrics = self._load_metrics()

            task_record = {
                "task_id": task_id,
                "user_id": user_id,
                "agent_type": agent_type,
                "query": query,
                "execution_time": execution_time,
                "success": success,
                "result_summary": result_summary,
                "timestamp": datetime.utcnow().isoformat()
            }

            if "tasks" not in metrics:
                metrics["tasks"] = []
            metrics["tasks"].append(task_record)

            # Keep only last 1000 tasks
            metrics["tasks"] = metrics["tasks"][-1000:]

            self._save_metrics(metrics)
            logger.info(f"Recorded task metrics: {task_id}")

        except Exception as e:
            logger.error(f"Failed to record task metrics: {e}")

    def get_agent_performance(self) -> Dict[str, Any]:
        """Get performance metrics for each agent"""
        try:
            metrics = self._load_metrics()
            tasks = metrics.get("tasks", [])

            agent_stats = {}
            total_tasks = len(tasks)

            for task in tasks:
                agent = task.get("agent_type", "unknown")
                if agent not in agent_stats:
                    agent_stats[agent] = {
                        "total_tasks": 0,
                        "successful_tasks": 0,
                        "avg_execution_time": 0.0,
                        "success_rate": 0.0
                    }

                agent_stats[agent]["total_tasks"] += 1
                if task.get("success", False):
                    agent_stats[agent]["successful_tasks"] += 1

                # Update average execution time
                current_avg = agent_stats[agent]["avg_execution_time"]
                count = agent_stats[agent]["total_tasks"]
                new_time = task.get("execution_time", 0.0)
                agent_stats[agent]["avg_execution_time"] = (current_avg * (count - 1) + new_time) / count

            # Calculate success rates
            for agent, stats in agent_stats.items():
                if stats["total_tasks"] > 0:
                    stats["success_rate"] = stats["successful_tasks"] / stats["total_tasks"]

            return {
                "total_tasks": total_tasks,
                "agent_performance": agent_stats,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get agent performance: {e}")
            return {"error": str(e)}

    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        try:
            metrics = self._load_metrics()
            tasks = metrics.get("tasks", [])

            user_tasks = [t for t in tasks if t.get("user_id") == user_id]

            if not user_tasks:
                return {"user_id": user_id, "total_tasks": 0, "analytics": {}}

            agent_usage = {}
            total_time = 0.0
            successful_tasks = 0

            for task in user_tasks:
                agent = task.get("agent_type", "unknown")
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
                total_time += task.get("execution_time", 0.0)
                if task.get("success", False):
                    successful_tasks += 1

            return {
                "user_id": user_id,
                "total_tasks": len(user_tasks),
                "successful_tasks": successful_tasks,
                "success_rate": successful_tasks / len(user_tasks) if user_tasks else 0,
                "total_execution_time": total_time,
                "avg_execution_time": total_time / len(user_tasks) if user_tasks else 0,
                "agent_usage": agent_usage,
                "last_task": user_tasks[-1]["timestamp"] if user_tasks else None
            }

        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {"error": str(e)}

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        try:
            performance = self.get_agent_performance()

            # Check recent task success rate (last 24 hours)
            metrics = self._load_metrics()
            tasks = metrics.get("tasks", [])

            # Filter tasks from last 24 hours
            cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_tasks = [
                t for t in tasks
                if datetime.fromisoformat(t["timestamp"]) > cutoff
            ]

            recent_success = sum(1 for t in recent_tasks if t.get("success", False))
            recent_success_rate = recent_success / len(recent_tasks) if recent_tasks else 1.0

            return {
                "overall_health": "healthy" if recent_success_rate > 0.8 else "degraded",
                "recent_success_rate": recent_success_rate,
                "recent_tasks": len(recent_tasks),
                "agent_performance": performance,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {"error": str(e)}

    def get_user_stats(self, user_id: str) -> dict:
        """Get comprehensive user statistics from database"""
        try:
            stats = self.profile_manager.get_user_stats(user_id)

            # Flatten the nested structure for easier access
            task_stats = stats.get('task_stats', {})
            job_stats = stats.get('job_stats', {})

            return {
                "total_tasks": task_stats.get('total_tasks', 0) or 0,
                "successful_tasks": task_stats.get('successful_tasks', 0) or 0,
                "failed_tasks": (task_stats.get('total_tasks', 0) or 0) - (task_stats.get('successful_tasks', 0) or 0),
                "total_execution_time": (task_stats.get('avg_response_time', 0.0) or 0.0) * (task_stats.get('total_tasks', 0) or 0),
                "job_applications": job_stats.get('total_applications', 0) or 0,
                "last_activity": stats.get('last_activity')
            }
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "total_execution_time": 0.0,
                "job_applications": 0,
                "last_activity": None
            }

    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from file"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
        return {}

    def _save_metrics(self, metrics: Dict[str, Any]):
        """Save metrics to file"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")


# Global instance
monitoring_system = MonitoringSystem()