import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
import json
import time

# Ensure project root is in Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

app = FastAPI(title='AI Agent Platform', version='4.0.0')

# Mount static files
static_dir = os.path.join(project_root, 'frontend from google ai studio')
if os.path.exists(static_dir):
    app.mount('/static', StaticFiles(directory=static_dir), name='static')
    print('Static files mounted successfully')

# Simple in-memory user storage for demo
users_db = {}

class ExecuteRequest(BaseModel):
    query: str
    user_id: str = "anonymous"
    context: Optional[Dict] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""

@app.get('/')
async def root():
    index_path = os.path.join(static_dir, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    return {"message": "AI Agent Platform", "status": "running"}

@app.get('/app')
async def app_page():
    app_path = os.path.join(static_dir, 'app.html')
    if os.path.exists(app_path):
        return FileResponse(app_path, media_type='text/html')
    return {"message": "App page not found"}

@app.get('/health')
async def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.get('/agents')
async def list_agents():
    agents = [
        {"name": "Search Agent", "type": "search", "description": "Information seeking and research"},
        {"name": "Career Agent", "type": "career", "description": "Job search and auto-application"},
        {"name": "Travel Agent", "type": "travel", "description": "Transportation and planning"},
        {"name": "Local Agent", "type": "local", "description": "Local services and recommendations"},
        {"name": "Transaction Agent", "type": "transaction", "description": "Shopping and purchases"},
        {"name": "Communication Agent", "type": "communication", "description": "Messaging and calls"},
        {"name": "Entertainment Agent", "type": "entertainment", "description": "Movies, music, games"},
        {"name": "Productivity Agent", "type": "productivity", "description": "Task management"},
        {"name": "Monitoring Agent", "type": "monitoring", "description": "Alerts and tracking"},
        {"name": "Browser Agent", "type": "browser", "description": "Web automation"},
        {"name": "Common Crawl Agent", "type": "common_crawl", "description": "Data mining"}
    ]
    return {"agents": agents, "total": len(agents)}

@app.post('/execute')
async def execute(request: ExecuteRequest):
    # Simple mock response based on keywords
    query_lower = request.query.lower()

    if "job" in query_lower or "career" in query_lower:
        result = {"message": "Career agent would search for jobs", "query": request.query}
    elif "search" in query_lower or "find" in query_lower:
        result = {"message": "Search agent would perform web search", "query": request.query}
    elif "travel" in query_lower or "flight" in query_lower:
        result = {"message": "Travel agent would plan your trip", "query": request.query}
    else:
        result = {"message": f"Processing your request: {request.query}", "agent": "general"}

    return {
        "task_id": f"task_{int(time.time() * 1000)}",
        "agent": "mock_agent",
        "result": result,
        "execution_time": 0.5,
        "status": "success"
    }

@app.post('/api/v1/auth/register')
async def register(request: RegisterRequest):
    if request.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    users_db[request.email] = {
        "email": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "subscription": "free",
        "created_at": time.time()
    }

    return {
        "status": "success",
        "message": "User registered successfully",
        "user": users_db[request.email]
    }

@app.post('/api/v1/auth/login')
async def login(request: LoginRequest):
    if request.email not in users_db:
        # Auto-register for demo
        users_db[request.email] = {
            "email": request.email,
            "subscription": "free",
            "created_at": time.time()
        }

    return {
        "status": "success",
        "message": "Login successful",
        "user": users_db[request.email]
    }

if __name__ == '__main__':
    print('Starting Simple AI Agent Platform server...')
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')