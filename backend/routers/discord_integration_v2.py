from fastapi import APIRouter, HTTPException, status, Depends, Header, Request
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

from database import get_database
from middleware.auth import get_current_active_user, require_site_admin
from services.discord_service import DiscordService
from models.discord_integration import (
    DiscordGuildCreate, DiscordGuildResponse, DiscordJobResponse,
    WebhookPayload, EventAnnouncementRequest, TournamentAnnouncementRequest,
    MessageSyncRequest, ReminderConfigResponse, DiscordIntegrationStats,
    WebhookEvent, WebhookType
)
from models.user import User

router = APIRouter()
discord_service = DiscordService()

# Bot API Endpoints
@router.post("/bot/verify")
async def verify_bot_authentication(
    guild_id: str,
    api_key: str
):
    """Verify Discord bot API authentication"""
    is_valid = await discord_service.verify_bot_auth(guild_id, api_key)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid bot authentication")
    
    # Update last used timestamp
    db = get_database()
    await db.discord_guilds.update_one(
        {"guild_id": guild_id},
        {"$set": {"last_sync_at": datetime.utcnow()}}
    )
    
    return {
        "status": "success",
        "message": "Bot verified successfully",
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": "v1",
        "guild_id": guild_id
    }

@router.post("/bot/guild/{guild_id}/register")
async def register_guild_by_bot(guild_id: str, guild_data: dict):
    """Register a guild via bot"""
    try:
        db = get_database()
        
        # Create guild document
        guild_doc = {
            "id": f"guild_{guild_id}",
            "guild_id": guild_id,
            "guild_name": guild_data.get("guild_name", "Unknown Guild"),
            "guild_icon": guild_data.get("guild_icon"),
            "owner_id": guild_data.get("owner_id"),
            "member_count": guild_data.get("member_count", 0),
            "org_id": None,
            "status": "active",
            "sync_enabled": True,
            "reminder_enabled": True,
            "webhook_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "setup_by_user_id": guild_data.get("setup_by_user_id"),
            "bot_auto_registered": guild_data.get("bot_auto_registered", False)
        }
        
        # Insert or update
        await db.discord_guilds.replace_one(
            {"guild_id": guild_id},
            guild_doc,
            upsert=True
        )
        
        return {
            "message": f"Guild {guild_data.get('guild_name')} registered successfully",
            "guild_id": guild_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register guild: {str(e)}"
        )

@router.get("/bot/guild/{guild_id}/config")
async def get_bot_guild_config(
    guild_id: str,
    api_key: str
):
    """Get guild configuration for Discord bot"""
    # Verify bot authentication
    is_valid = await discord_service.verify_bot_auth(guild_id, api_key)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid bot authentication")
    
    guild = await discord_service.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    # Get reminder configurations
    db = get_database()
    reminder_configs = []
    async for config_doc in db.reminder_configs.find({"guild_id": guild_id}):
        reminder_configs.append(ReminderConfigResponse(
            id=config_doc["id"],
            guild_id=config_doc["guild_id"],
            reminder_type=config_doc["reminder_type"],
            enabled=config_doc["enabled"],
            channel_id=config_doc.get("channel_id"),
            custom_message=config_doc.get("custom_message"),
            offset_minutes=config_doc.get("offset_minutes", 0),
            created_at=config_doc["created_at"]
        ))
    
    return {
        "guild": {
            "id": guild.id,
            "guild_id": guild.guild_id,
            "guild_name": guild.guild_name,
            "sync_enabled": guild.sync_enabled,
            "reminder_enabled": guild.reminder_enabled,
            "announcement_channel_id": getattr(guild, 'announcement_channel_id', None),
            "reminder_channel_id": getattr(guild, 'reminder_channel_id', None)
        },
        "reminder_configs": reminder_configs
    }

# Guild Management Endpoints
@router.post("/guilds", response_model=DiscordGuildResponse)
async def register_discord_guild(
    guild_data: DiscordGuildCreate,
    org_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Register a new Discord guild for integration"""
    try:
        guild = await discord_service.register_guild(guild_data, org_id)
        
        # Get organization name if available
        org_name = None
        if org_id:
            db = get_database()
            org_doc = await db.organizations.find_one({"id": org_id})
            org_name = org_doc.get("name") if org_doc else None
        
        return DiscordGuildResponse(
            id=guild.id,
            guild_id=guild.guild_id,
            guild_name=guild.guild_name,
            owner_id=guild.owner_id,
            org_id=guild.org_id,
            org_name=org_name,
            status=guild.status,
            sync_enabled=guild.sync_enabled,
            reminder_enabled=guild.reminder_enabled,
            webhook_verified=guild.webhook_verified,
            last_sync_at=guild.last_sync_at,
            created_at=guild.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/guilds", response_model=List[DiscordGuildResponse])
async def list_discord_guilds(
    org_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """List Discord guilds (filtered by organization if specified)"""
    db = get_database()
    
    # Build query filter
    query_filter = {}
    if org_id:
        query_filter["org_id"] = org_id
    
    guilds = []
    async for guild_doc in db.discord_guilds.find(query_filter):
        # Get organization name if available
        org_name = None
        if guild_doc.get("org_id"):
            org_doc = await db.organizations.find_one({"id": guild_doc["org_id"]})
            org_name = org_doc.get("name") if org_doc else None
        
        guilds.append(DiscordGuildResponse(
            id=guild_doc["id"],
            guild_id=guild_doc["guild_id"],
            guild_name=guild_doc["guild_name"],
            owner_id=guild_doc["owner_id"],
            org_id=guild_doc.get("org_id"),
            org_name=org_name,
            status=guild_doc["status"],
            sync_enabled=guild_doc["sync_enabled"],
            reminder_enabled=guild_doc["reminder_enabled"],
            webhook_verified=guild_doc["webhook_verified"],
            last_sync_at=guild_doc.get("last_sync_at"),
            created_at=guild_doc["created_at"]
        ))
    
    return guilds

@router.get("/guilds/{guild_id}", response_model=DiscordGuildResponse)
async def get_discord_guild(
    guild_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get Discord guild details"""
    guild = await discord_service.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    # Get organization name if available
    org_name = None
    if guild.org_id:
        db = get_database()
        org_doc = await db.organizations.find_one({"id": guild.org_id})
        org_name = org_doc.get("name") if org_doc else None
    
    return DiscordGuildResponse(
        id=guild.id,
        guild_id=guild.guild_id,
        guild_name=guild.guild_name,
        owner_id=guild.owner_id,
        org_id=guild.org_id,
        org_name=org_name,
        status=guild.status,
        sync_enabled=guild.sync_enabled,
        reminder_enabled=guild.reminder_enabled,
        webhook_verified=guild.webhook_verified,
        last_sync_at=guild.last_sync_at,
        created_at=guild.created_at
    )

# Webhook Endpoints
@router.post("/webhooks/incoming")
async def receive_discord_webhook(
    request: Request,
    x_signature_256: Optional[str] = Header(None)
):
    """Receive webhook from Discord bot"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature if provided
        if x_signature_256:
            if not await discord_service.verify_webhook_signature(body, x_signature_256):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse JSON payload
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Process webhook
        result = await discord_service.process_incoming_webhook(payload)
        
        return {
            "status": "received",
            "processed": result.get("status") == "processed",
            "message": result.get("reason", "Webhook processed successfully")
        }
        
    except Exception as e:
        await discord_service.log_webhook(
            webhook_data={"error": str(e)},
            webhook_type=WebhookType.INCOMING,
            event_type=WebhookEvent.MESSAGE_CREATE,  # Default event type for errors
            response_code=500,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

# Event and Tournament Announcements
@router.post("/announce/event")
async def announce_event_to_discord(
    announcement: EventAnnouncementRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send event announcement to Discord guilds"""
    try:
        await discord_service.announce_event(
            event_id=announcement.event_id,
            announcement_type=announcement.announcement_type,
            guild_ids=announcement.guild_ids
        )
        
        return {
            "message": "Event announcement queued",
            "event_id": announcement.event_id,
            "guild_ids": announcement.guild_ids,
            "type": announcement.announcement_type
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue announcement: {str(e)}")

@router.post("/announce/tournament")
async def announce_tournament_to_discord(
    announcement: TournamentAnnouncementRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send tournament announcement to Discord guilds"""
    try:
        await discord_service.announce_tournament(
            tournament_id=announcement.tournament_id,
            announcement_type=announcement.announcement_type,
            guild_ids=announcement.guild_ids
        )
        
        return {
            "message": "Tournament announcement queued",
            "tournament_id": announcement.tournament_id,
            "guild_ids": announcement.guild_ids,
            "type": announcement.announcement_type
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue announcement: {str(e)}")

# Message Synchronization
@router.post("/sync/message")
async def sync_message_across_guilds(
    sync_request: MessageSyncRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Synchronize message across multiple Discord guilds"""
    try:
        await discord_service.sync_message(
            source_guild_id=sync_request.source_guild_id,
            target_guild_ids=sync_request.target_guild_ids,
            message_content=sync_request.message_content,
            author_name=sync_request.author_name,
            channel_type=sync_request.channel_type
        )
        
        return {
            "message": "Message synchronization queued",
            "source_guild_id": sync_request.source_guild_id,
            "target_guild_ids": sync_request.target_guild_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue message sync: {str(e)}")

# Reminder Management
@router.post("/reminders/schedule/{event_id}")
async def schedule_event_reminders(
    event_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Schedule automatic reminders for an event"""
    try:
        await discord_service.schedule_event_reminders(event_id)
        return {
            "message": "Event reminders scheduled",
            "event_id": event_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule reminders: {str(e)}")

# Job Management (Admin only)
@router.get("/jobs", response_model=List[DiscordJobResponse])
async def list_discord_jobs(
    limit: int = 50,
    status: Optional[str] = None,
    admin_user: User = Depends(require_site_admin)
):
    """List Discord jobs (admin only)"""
    db = get_database()
    
    # Build query filter
    query_filter = {}
    if status:
        query_filter["status"] = status
    
    jobs = []
    async for job_doc in db.discord_jobs.find(query_filter).limit(limit).sort("created_at", -1):
        jobs.append(DiscordJobResponse(
            id=job_doc["id"],
            job_type=job_doc["job_type"],
            guild_id=job_doc["guild_id"],
            event_id=job_doc.get("event_id"),
            status=job_doc["status"],
            retry_count=job_doc["retry_count"],
            max_retries=job_doc["max_retries"],
            scheduled_at=job_doc["scheduled_at"],
            created_at=job_doc["created_at"],
            started_at=job_doc.get("started_at"),
            completed_at=job_doc.get("completed_at"),
            error_message=job_doc.get("error_message")
        ))
    
    return jobs

@router.post("/jobs/process")
async def process_discord_jobs(
    admin_user: User = Depends(require_site_admin)
):
    """Manually trigger job processing (admin only)"""
    try:
        await discord_service.process_jobs()
        return {"message": "Job processing triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job processing failed: {str(e)}")

# Statistics and Monitoring
@router.get("/stats", response_model=DiscordIntegrationStats)
async def get_discord_integration_stats(
    admin_user: User = Depends(require_site_admin)
):
    """Get Discord integration statistics (admin only)"""
    stats = await discord_service.get_integration_stats()
    return DiscordIntegrationStats(**stats)

# Health Check
@router.get("/health")
async def discord_integration_health():
    """Health check for Discord integration system"""
    try:
        stats = await discord_service.get_integration_stats()
        
        return {
            "status": "healthy",
            "webhook_secret_configured": bool(discord_service.webhook_secret),
            "bot_api_configured": bool(discord_service.bot_api_base_url and discord_service.bot_api_token),
            "guilds_registered": stats.get("total_guilds", 0),
            "active_guilds": stats.get("active_guilds", 0),
            "pending_jobs": stats.get("pending_jobs", 0),
            "message": "Discord integration system operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Discord integration system experiencing issues"
        }

# Legacy endpoints for backward compatibility
@router.post("/events/announce")
async def legacy_event_announce(
    payload: Dict[str, Any],
    x_signature_256: Optional[str] = Header(None)
):
    """Legacy webhook endpoint for Discord bot to announce events"""
    # Log webhook for compatibility
    await discord_service.log_webhook(
        webhook_data=payload,
        webhook_type=WebhookType.INCOMING,
        event_type=WebhookEvent.EVENT_CREATED,
        response_code=200
    )
    
    return {"message": "Event announcement received (legacy)", "payload": payload}

@router.post("/matches/announce")
async def legacy_match_announce(
    payload: Dict[str, Any],
    x_signature_256: Optional[str] = Header(None)
):
    """Legacy webhook endpoint for Discord bot to announce matches"""
    # Log webhook for compatibility
    await discord_service.log_webhook(
        webhook_data=payload,
        webhook_type=WebhookType.INCOMING,
        event_type=WebhookEvent.MATCH_RESULT,
        response_code=200
    )
    
    return {"message": "Match announcement received (legacy)", "payload": payload}