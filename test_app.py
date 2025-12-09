from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Starting up')
    yield
    print('Shutting down')

app = FastAPI(lifespan=lifespan)

@app.get('/')
async def root():
    return {'message': 'Hello World'}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
