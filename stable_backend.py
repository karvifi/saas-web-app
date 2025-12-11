"""
AI Agent Platform - STABLE BACKEND
Minimal working version with core functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import asyncio
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="AI Agent Platform",
    description="Stable backend for AI Agent Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Serve static files
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend from google ai studio")
# if os.path.exists(frontend_dir):
#     app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Pydantic models
class TaskRequest(BaseModel):
    query: str
    user_id: str = "anonymous"
    context: Optional[Dict] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    agent: str
    execution_time: float
    result: Any
    error: Optional[str] = None

# Simple agent implementations (inline for stability)
class SimpleSearchAgent:
    def __init__(self):
        self.name = "search"

    async def search(self, query: str) -> Dict:
        # Simple mock search result
        await asyncio.sleep(0.5)  # Simulate processing time
        return {
            "query": query,
            "results": [
                {"title": f"Result 1 for {query}", "url": "https://example.com/1", "snippet": "Sample result"},
                {"title": f"Result 2 for {query}", "url": "https://example.com/2", "snippet": "Another result"}
            ],
            "total_results": 2
        }

class SimpleCareerAgent:
    def __init__(self):
        self.name = "career"

    async def search_jobs(self, query: str) -> Dict:
        await asyncio.sleep(0.5)
        return {
            "query": query,
            "jobs_found": 3,
            "jobs": [
                {"title": f"Software Engineer - {query}", "company": "Tech Corp", "location": "Remote", "salary": "$80k-100k"},
                {"title": f"Product Manager - {query}", "company": "Startup Inc", "location": "San Francisco", "salary": "$120k-150k"},
                {"title": f"Data Scientist - {query}", "company": "Data Co", "location": "New York", "salary": "$90k-120k"}
            ]
        }

# Initialize agents
search_agent = SimpleSearchAgent()
career_agent = SimpleCareerAgent()

# Routes
@app.get("/")
async def root():
    """Serve the landing page"""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "AI Agent Platform", "status": "running"}

@app.get("/app")
async def app_page():
    """Serve the main app page"""
    app_path = os.path.join(frontend_dir, "app.html")
    if os.path.exists(app_path):
        return FileResponse(app_path, media_type="text/html")
    return {"message": "App page not found", "status": "error"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/execute")
async def execute_task(request: TaskRequest):
    """Execute a task using AI agents"""
    start_time = datetime.utcnow()
    task_id = f"task_{int(start_time.timestamp() * 1000)}"

    try:
        # Simple keyword-based routing
        query_lower = request.query.lower()
        agent_name = "search"  # default

        if any(word in query_lower for word in ["job", "career", "apply", "resume"]):
            agent_name = "career"
        elif any(word in query_lower for word in ["search", "find", "lookup"]):
            agent_name = "search"

        # Execute task
        if agent_name == "search":
            result = await search_agent.search(request.query)
        elif agent_name == "career":
            result = await career_agent.search_jobs(request.query)
        else:
            result = {"error": "No suitable agent found"}

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return TaskResponse(
            task_id=task_id,
            status="success",
            agent=agent_name,
            execution_time=execution_time,
            result=result
        )

    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return TaskResponse(
            task_id=task_id,
            status="error",
            agent=agent_name,
            execution_time=execution_time,
            result=None,
            error=str(e)
        )

@app.get("/agents")
async def list_agents():
    """List available agents"""
    return {
        "agents": [
            {"name": "Search Agent", "type": "search", "description": "Information search and retrieval"},
            {"name": "Career Agent", "type": "career", "description": "Job search and career assistance"}
        ]
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": exc.detail, "status_code": exc.status_code}

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {"error": "Internal server error", "details": str(exc)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Agent Platform Backend...")
    print("📁 Frontend directory:", frontend_dir)
    print("🔍 Frontend exists:", os.path.exists(frontend_dir))
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")