from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
import os
from datetime import datetime

app = FastAPI(title='AI Agent Platform', version='4.0.0')

# Mount static files
app.mount('/static', StaticFiles(directory=os.path.join(os.path.dirname(__file__), '..', 'frontend')), name='static')

class ExecuteRequest(BaseModel):
    query: str
    user_id: Optional[str] = 'anonymous'
    context: Optional[Dict] = None

@app.get('/')
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html'))

@app.get('/app')
async def app_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'app.html'))

@app.post('/execute')
async def execute(request: ExecuteRequest):
    # Simple mock response for now
    return {'result': f'Query processed: {request.query}'}

@app.get('/stats')
async def stats():
    return {'agents': 0, 'status': 'minimal server running'}

@app.get('/pricing')
async def pricing():
    return {'plans': []}

@app.post('/subscribe')
async def subscribe(user_id: str, plan: str, email: str):
    return {'checkout_url': 'mock_url'}

@app.get('/subscription/{user_id}')
async def subscription(user_id: str):
    return {'status': 'mock_status'}

@app.post('/webhook/stripe')
async def stripe_webhook(data: Dict):
    return {'status': 'ok'}
