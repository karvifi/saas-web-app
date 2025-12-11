import os
import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional

# Ensure project root is in Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

app = FastAPI(title='AI Agent Platform', version='4.0.0')

class ExecuteRequest(BaseModel):
    query: str
    user_id: Optional[str] = 'anonymous'
    context: Optional[Dict] = None

@app.get('/')
async def root():
    return {'message': 'AI Agent Platform API', 'status': 'running'}

@app.post('/execute')
async def execute(request: ExecuteRequest):
    return {'result': f'Query processed: {request.query}'}

@app.get('/stats')
async def stats():
    return {'agents': 0, 'status': 'server running'}

@app.get('/health')
async def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    print('Starting AI Agent Platform server...')
    uvicorn.run(
        'start_server:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level='info'
    )
