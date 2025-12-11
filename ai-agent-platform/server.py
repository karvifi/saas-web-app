import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
import traceback

# Ensure project root is in Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

app = FastAPI(title='AI Agent Platform', version='4.0.0')

# Try to mount static files
try:
    static_dir = os.path.join(project_root, 'frontend from google ai studio')
    if os.path.exists(static_dir):
        app.mount('/static', StaticFiles(directory=static_dir), name='static')
        print('Static files mounted successfully from frontend directory')
    else:
        print('Frontend directory not found, static files not mounted')
except Exception as e:
    print('Warning: Could not mount static files:', e)

# Also try to mount the regular frontend
try:
    static_dir = os.path.join(project_root, 'frontend')
    if os.path.exists(static_dir):
        app.mount('/oldstatic', StaticFiles(directory=static_dir), name='oldstatic')
        print('Old static files mounted successfully')
except Exception as e:
    print('Warning: Could not mount old static files:', e)

class ExecuteRequest(BaseModel):
    query: str
    user_id: Optional[str] = 'anonymous'
    context: Optional[Dict] = None

# Agent imports with error handling
agents_available = []
agents_dict = {}

# Initialize UserProfileManager
profile_manager = None
try:
    from backend.user_profiles import UserProfileManager
    profile_manager = UserProfileManager()
    print('UserProfileManager loaded successfully')
except Exception as e:
    print('Warning: Could not load UserProfileManager:', e)
    profile_manager = None


# Try to load individual agents first
agent_classes = [
    ('search', 'agents.search', 'SearchAgent'),
    ('career', 'agents.career', 'CareerAgent'),
    ('travel', 'agents.travel', 'TravelAgent'),
    ('local', 'agents.local', 'LocalAgent'),
    ('transaction', 'agents.transaction', 'TransactionAgent'),
    ('communication', 'agents.communication', 'CommunicationAgent'),
    ('entertainment', 'agents.entertainment', 'EntertainmentAgent'),
    ('productivity', 'agents.productivity', 'ProductivityAgent'),
    ('monitoring', 'agents.monitoring', 'MonitoringAgent'),
    ('browser', 'agents.browser_advanced', 'AdvancedBrowserAgent'),
    ('common_crawl', 'agents.common_crawl', 'CommonCrawlAgent'),
]

for agent_name, module_name, class_name in agent_classes:
    try:
        module = __import__(module_name, fromlist=[class_name])
        agent_class = getattr(module, class_name)
        agent_instance = agent_class()
        agents_dict[agent_name] = agent_instance
        agents_available.append(agent_name)
        print(f'{agent_name} agent loaded successfully')
    except Exception as e:
        print(f'Warning: Could not load {agent_name} agent:', e)

# Now instantiate orchestrator with loaded agents
orchestrator = None
try:
    from agents.orchestrator_advanced import AdvancedOrchestrator
    orchestrator = AdvancedOrchestrator(agents=agents_dict)
    print('Orchestrator loaded successfully')
except Exception as e:
    print('Warning: Could not load orchestrator:', e)
    orchestrator = None

@app.get('/')
async def root():
    try:
        index_path = os.path.join(project_root, 'frontend from google ai studio', 'index.html')
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            return {'message': 'AI Agent Platform API', 'status': 'running', 'agents_loaded': len(agents_available)}
    except Exception as e:
        return {'message': 'AI Agent Platform API', 'status': 'running', 'error': str(e)}

@app.get('/app')
async def app_page():
    try:
        app_path = os.path.join(project_root, 'frontend from google ai studio', 'app.html')
        if os.path.exists(app_path):
            return FileResponse(app_path)
        else:
            return {'message': 'App page not found', 'status': 'error'}
    except Exception as e:
        return {'message': 'Error loading app page', 'error': str(e)}

@app.post('/execute')
async def execute(request: ExecuteRequest):
    if orchestrator:
        try:
            result = await orchestrator.execute(request.query, request.user_id, request.context)
            return {'result': result}
        except Exception as e:
            return {'error': f'Execution failed: {str(e)}', 'agents_available': agents_available}
    else:
        return {'result': f'Mock response: {request.query}', 'note': 'Orchestrator not available', 'agents_available': agents_available}

@app.get('/stats')
async def stats():
    return {
        'agents': len(agents_available),
        'agents_available': agents_available,
        'orchestrator_loaded': orchestrator is not None,
        'status': 'running'
    }

@app.get('/health')
async def health():
    return {'status': 'healthy', 'agents_loaded': len(agents_available)}



# User Profile API Endpoints
@app.get('/api/v1/users/{user_id}')
async def get_user_profile(user_id: str):
    """Get user profile"""
    if not profile_manager:
        raise HTTPException(status_code=503, detail="User profile service not available")

    try:
        profile = profile_manager.get_user(user_id)
        return {'profile': profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

@app.put('/api/v1/users/{user_id}')
async def update_user_profile(user_id: str, updates: Dict):
    """Update user profile"""
    if not profile_manager:
        raise HTTPException(status_code=503, detail="User profile service not available")

    try:
        updated_profile = profile_manager.update_user(user_id, updates)
        return {'profile': updated_profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")

@app.get('/api/v1/users/{user_id}/stats')
async def get_user_stats(user_id: str):
    """Get user statistics"""
    if not profile_manager:
        raise HTTPException(status_code=503, detail="User profile service not available")

    try:
        stats = profile_manager.get_user_stats(user_id)
        return {'stats': stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")

@app.get('/api/v1/users')
async def list_users():
    """List all user IDs"""
    if not profile_manager:
        raise HTTPException(status_code=503, detail="User profile service not available")

    try:
        users = profile_manager.get_all_users()
        return {'users': users, 'count': len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")

# Authentication endpoints
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""

@app.post('/api/v1/auth/register')
async def register(request: RegisterRequest):
    """Register new user"""
    if not profile_manager:
        raise HTTPException(status_code=503, detail="User profile service not available")

    try:
        # Check if user already exists
        existing = profile_manager.get_profile(request.email)
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        # Create user profile
        user_profile = profile_manager.create_profile(request.email, {
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "subscription": "free"
        })

        return {
            "status": "success",
            "message": "User registered successfully",
            "user": user_profile
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post('/api/v1/auth/login')
async def login(request: LoginRequest):
    """Login user"""
    if not profile_manager:
        raise HTTPException(status_code=503, detail="User profile service not available")

    try:
        user_profile = profile_manager.get_profile(request.email)
        if not user_profile:
            # Auto-register new users
            user_profile = profile_manager.create_profile(request.email, {
                "email": request.email,
                "subscription": "free"
            })

        return {
            "status": "success",
            "message": "Login successful",
            "user": user_profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

if __name__ == '__main__':
    print('Starting AI Agent Platform server...')
    print(f'Agents loaded: {agents_available}')
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')


