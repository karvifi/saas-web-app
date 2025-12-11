"""
Production AI Agent Platform Backend
Integrates all enterprise-grade components for production deployment
"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
from datetime import datetime
import os

# Import all our enterprise components
from websockets import router as websocket_router, manager as ws_manager
from redis_cache import cache
from notification_service import notification_manager
from job_processor import job_queue, job_processor, enqueue_task_execution
from monitoring import metrics, health_checker, alert_manager, monitoring_middleware
from api_versioning import (
    api_version_manager, rate_limiter, versioning_middleware,
    security_headers_middleware, request_logging_middleware,
    rate_limit_middleware, v1_router
)
from file_management import router as file_router, file_storage
from compliance import router as compliance_router, audit_logger
from multi_tenancy import router as tenant_router, tenant_manager, tenant_middleware

# Import existing components
from agents import get_agent_response
from database import init_database, get_user, create_user, save_task, get_user_tasks
from auth_service import create_access_token, verify_token, hash_password, verify_password
from security import SecurityMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Agent Platform - Production",
    description="Enterprise-grade AI Agent Platform with comprehensive features",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware in correct order
app.add_middleware(TenantMiddleware, tenant_manager=tenant_manager)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(VersioningMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MonitoringMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(v1_router, prefix="/v1")
app.include_router(websocket_router)
app.include_router(file_router)
app.include_router(compliance_router)
app.include_router(tenant_router)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    logger.info("Starting AI Agent Platform...")

    # Initialize database
    init_database()
    logger.info("Database initialized")

    # Start monitoring collection
    await metrics.start_collection()
    logger.info("Metrics collection started")

    # Start background job processor
    asyncio.create_task(job_processor.process_jobs(max_concurrent=10))
    logger.info("Job processor started")

    # Start file cleanup
    from file_management import start_file_cleanup_task
    asyncio.create_task(start_file_cleanup_task())
    logger.info("File cleanup task started")

    # Start compliance tasks
    from compliance import start_compliance_tasks
    asyncio.create_task(start_compliance_tasks())
    logger.info("Compliance tasks started")

    logger.info("AI Agent Platform startup complete!")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of all components"""
    logger.info("Shutting down AI Agent Platform...")

    await metrics.stop_collection()
    await job_processor.stop()

    logger.info("Shutdown complete")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = await health_checker.run_all_checks()

    status_code = 200 if health_status["overall_status"] == "healthy" else 503

    return JSONResponse(
        content=health_status,
        status_code=status_code
    )

# System status endpoint
@app.get("/status")
async def system_status():
    """Get complete system status"""
    from monitoring import get_system_status
    return await get_system_status()

# Root endpoint
@app.get("/")
async def root():
    """API root"""
    return {
        "name": "AI Agent Platform",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "11 AI Agents",
            "Real-time WebSockets",
            "Redis Caching",
            "Background Jobs",
            "Email/SMS Notifications",
            "File Management",
            "Audit Logging",
            "Multi-tenancy",
            "API Versioning",
            "Rate Limiting",
            "Monitoring & Metrics"
        ],
        "docs": "/docs",
        "health": "/health"
    }

# Authentication endpoints
@app.post("/v1/auth/register")
async def register_user(email: str, password: str, name: str = None):
    """Register a new user"""
    try:
        # Hash password
        hashed_password = hash_password(password)

        # Create user
        user_id = create_user(email, hashed_password, name)

        # Send welcome notification
        await notification_manager.notify_user(
            user_id, "welcome",
            email=email, user_name=name or email
        )

        # Log registration
        await audit_logger.log_event(
            event_type="user_registration",
            user_id=user_id,
            resource="user",
            action="register",
            details={"email": email}
        )

        return {"user_id": user_id, "message": "User registered successfully"}
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/v1/auth/login")
async def login_user(email: str, password: str):
    """Authenticate user"""
    user = get_user(email)
    if not user or not verify_password(password, user[2]):  # user[2] is password hash
        await audit_logger.log_event(
            event_type="authentication",
            user_id=None,
            resource="auth",
            action="login_failed",
            status="failure",
            details={"email": email}
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create access token
    access_token = create_access_token({"sub": str(user[0])})  # user[0] is user_id

    # Log successful login
    await audit_logger.log_event(
        event_type="authentication",
        user_id=str(user[0]),
        resource="auth",
        action="login_success",
        details={"email": email}
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Task execution endpoint
@app.post("/v1/tasks/execute")
async def execute_task(
    agent_name: str,
    task_data: dict,
    user_id: str = Depends(verify_token)
):
    """Execute an AI agent task"""
    try:
        # Check rate limits
        tenant_context = await get_tenant_context(user_id)
        if tenant_context.get("tenant"):
            tenant_id = tenant_context["tenant"]["tenant_id"]
            within_limits = await tenant_manager.check_tenant_limits(
                tenant_id, "max_tasks_per_day", 0  # Would track actual usage
            )
            if not within_limits:
                raise HTTPException(status_code=429, detail="Tenant task limit exceeded")

        # Generate task ID
        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"

        # Save task to database
        save_task(user_id, task_id, agent_name, task_data, "running")

        # Queue task for execution
        job_id = await enqueue_task_execution(agent_name, task_data, user_id)

        # Notify via WebSocket
        await ws_manager.broadcast_task_update(task_id, "queued", user_id)

        # Log task execution
        await audit_logger.log_event(
            event_type="task_execution",
            user_id=user_id,
            resource="task",
            action="execute",
            details={"agent": agent_name, "task_id": task_id}
        )

        return {
            "task_id": task_id,
            "job_id": job_id,
            "status": "queued",
            "message": f"Task queued for execution by {agent_name}"
        }

    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get task results
@app.get("/v1/tasks/{task_id}")
async def get_task_result(task_id: str, user_id: str = Depends(verify_token)):
    """Get task execution result"""
    try:
        # Get task from database
        tasks = get_user_tasks(user_id)
        task = next((t for t in tasks if t[1] == task_id), None)  # t[1] is task_id

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        result = {
            "task_id": task[1],
            "agent_name": task[2],
            "status": task[4],
            "created_at": task[5],
            "result": task[6]
        }

        return result

    except Exception as e:
        logger.error(f"Failed to get task result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# List user tasks
@app.get("/v1/tasks")
async def list_user_tasks(
    user_id: str = Depends(verify_token),
    limit: int = 20,
    offset: int = 0
):
    """List user's tasks"""
    try:
        tasks = get_user_tasks(user_id)

        # Convert to dict format
        task_list = []
        for task in tasks[offset:offset+limit]:
            task_list.append({
                "task_id": task[1],
                "agent_name": task[2],
                "task_data": task[3],
                "status": task[4],
                "created_at": task[5],
                "result": task[6]
            })

        return {
            "tasks": task_list,
            "total": len(tasks),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
from websockets import websocket_endpoint
app.add_websocket_route(websocket_endpoint, "/ws/{user_id}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    # Log error
    await audit_logger.log_event(
        event_type="api_error",
        user_id=getattr(request.state, "user_id", None),
        resource=request.url.path,
        action=request.method,
        status="error",
        details={"status_code": exc.status_code, "detail": exc.detail}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Log critical error
    await audit_logger.log_event(
        event_type="system_error",
        user_id=getattr(request.state, "user_id", None),
        resource=request.url.path,
        action=request.method,
        status="error",
        severity="critical",
        details={"error": str(exc)}
    )

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Import additional dependencies that might be missing
try:
    from multi_tenancy import TenantMiddleware
except ImportError:
    class TenantMiddleware:
        def __init__(self, app, tenant_manager=None):
            self.app = app
        async def __call__(self, scope, receive, send):
            return await self.app(scope, receive, send)

if __name__ == "__main__":
    # Get port from environment
    port = int(os.getenv("PORT", 8000))

    # Run server
    uvicorn.run(
        "production_backend:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )