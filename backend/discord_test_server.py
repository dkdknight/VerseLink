#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
import asyncio

# Create app without lifespan to avoid middleware issues
app = FastAPI(
    title="VerseLink Discord Test API",
    description="Test server for Discord integration",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routers import discord_events

# Include only Discord Events router for testing
app.include_router(discord_events.router, prefix="/api/v1/discord/events", tags=["Discord Events"])

@app.get("/")
async def root():
    return {"message": "VerseLink Discord Test API", "status": "active"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "Discord Test API"}

@app.on_event("startup")
async def startup_event():
    await init_db()
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)