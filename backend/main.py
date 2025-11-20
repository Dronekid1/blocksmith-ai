from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from api import generations, credits, webhooks, users
from services.supabase_client import get_supabase_client

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("BlockSmith AI Backend Starting...")
    yield
    # Shutdown
    print("BlockSmith AI Backend Shutting Down...")

app = FastAPI(
    title="BlockSmith AI",
    description="AI-powered Minecraft plugin, datapack, and texture pack generator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "https://blocksmith.ai",  # Update with your domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(generations.router, prefix="/api/generations", tags=["generations"])
app.include_router(credits.router, prefix="/api/credits", tags=["credits"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

@app.get("/")
async def root():
    return {
        "name": "BlockSmith AI API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
