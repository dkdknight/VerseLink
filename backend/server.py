from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import motor.motor_asyncio
from decouple import config
import logging

from routers import auth, users, organizations, events, tournaments, discord_integration, discord_integration_v2, notifications, moderation
from database import init_db
from middleware.auth import get_current_user
from services.discord_scheduler import start_discord_scheduler, stop_discord_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Application shutting down")

app = FastAPI(
    title="VerseLink API",
    description="Plateforme Star Citizen pour corporations, événements et tournois",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# API Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(organizations.router, prefix="/api/v1/orgs", tags=["Organizations"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(tournaments.router, prefix="/api/v1/tournaments", tags=["Tournaments"])
app.include_router(discord_integration.router, prefix="/api/v1/integrations/discord", tags=["Discord Integration"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(moderation.router, prefix="/api/v1/moderation", tags=["Moderation"])

@app.get("/")
async def root():
    return {"message": "VerseLink API", "version": "1.0.0", "status": "active"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "VerseLink API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)