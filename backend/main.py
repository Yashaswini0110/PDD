from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app import storage
import asyncio

app = FastAPI(title="Contract Analyzer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def background_cleanup_task():
    while True:
        storage.delete_expired_files()
        await asyncio.sleep(3600)  # Sleep for 1 hour

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_cleanup_task())

app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
