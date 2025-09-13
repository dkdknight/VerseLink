from fastapi import APIRouter, HTTPException, status, Depends, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import hmac
import hashlib
import httpx
import json
import logging
from datetime import datetime
from decouple import config

from database import get_database
from middleware.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

DISCORD_BOT_WEBHOOK_SECRET = config("DISCORD_BOT_WEBHOOK_SECRET", default="your-super-secret-webhook-key-change-this-in-production")
DISCORD_BOT_WEBHOOK_URL = config("DISCORD_BOT_WEBHOOK_URL", default="http://localhost:8050/webhook")

# Modèles Pydantic pour les webhooks
class EventWebhookData(BaseModel):
    event: Dict[str, Any]
    org_id: str

class TournamentWebhookData(BaseModel):
    tournament: Dict[str, Any]
    org_id: str

class TestConnectionData(BaseModel):
    org_id: str
    test_type: str = "connection"  # connection, events_channel, tournaments_channel

class OrganizationDiscordConfig(BaseModel):
    discord_guild_id: str
    discord_guild_name: str
    events_channel_id: str
    events_channel_name: str
    tournaments_channel_id: Optional[str] = None
    tournaments_channel_name: Optional[str] = None
    auto_publish_events: bool = True
    auto_publish_tournaments: bool = True

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Discord webhook HMAC signature"""
    if not DISCORD_BOT_WEBHOOK_SECRET:
        return True  # Skip verification if no secret configured
    
    expected_signature = hmac.new(
        DISCORD_BOT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

@router.post("/events/announce")
async def discord_event_announce(
    payload: Dict[str, Any],
    x_signature_256: Optional[str] = Header(None)
):
    """Webhook endpoint for Discord bot to announce events"""
    # TODO: Implement signature verification
    # if x_signature_256 and not verify_webhook_signature(request.body, x_signature_256):
    #     raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Placeholder for Discord bot integration
    return {"message": "Event announcement received", "payload": payload}

@router.post("/matches/announce")
async def discord_match_announce(
    payload: Dict[str, Any],
    x_signature_256: Optional[str] = Header(None)
):
    """Webhook endpoint for Discord bot to announce matches"""
    # TODO: Implement signature verification
    
    # Placeholder for Discord bot integration
    return {"message": "Match announcement received", "payload": payload}

@router.post("/relay/event")
async def relay_event_to_discord(
    payload: Dict[str, Any],
    current_user = Depends(get_current_active_user)
):
    """API endpoint for site to request Discord bot to relay events"""
    # TODO: Implement actual Discord bot API calls
    
    required_fields = ["event_id", "targets", "action"]
    for field in required_fields:
        if field not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Validate action
    if payload["action"] not in ["create", "update", "delete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be create, update, or delete"
        )
    
    # TODO: Queue job to call Discord bot API
    return {
        "message": "Event relay queued",
        "event_id": payload["event_id"],
        "targets": payload["targets"],
        "action": payload["action"]
    }

@router.post("/relay/remind")
async def relay_reminder_to_discord(
    payload: Dict[str, Any],
    current_user = Depends(get_current_active_user)
):
    """API endpoint for site to request Discord bot to send reminders"""
    required_fields = ["event_id", "when"]
    for field in required_fields:
        if field not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Validate when
    if payload["when"] not in ["J-3", "J-1", "H-1", "custom"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="When must be J-3, J-1, H-1, or custom"
        )
    
    # TODO: Queue reminder job
    return {
        "message": "Reminder queued",
        "event_id": payload["event_id"],
        "when": payload["when"]
    }

@router.get("/health")
async def discord_integration_health():
    """Health check for Discord integration"""
    return {
        "status": "healthy",
        "webhook_secret_configured": bool(DISCORD_BOT_WEBHOOK_SECRET),
        "message": "Discord integration endpoints ready"
    }