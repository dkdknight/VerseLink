from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timedelta

from database import get_database
from middleware.auth import get_current_active_user, require_site_admin
from services.discord_service import DiscordService
from services.discord_events_service import DiscordEventsService
from models.discord_integration import (
    DiscordEventResponse, InteractionResponse, DiscordEventCreate,
    DiscordIntegrationStats, JobType, DiscordJobCreate
)
from models.user import User

router = APIRouter()
discord_service = DiscordService()
discord_events_service = DiscordEventsService()

# Discord Scheduled Events Management
@router.post("/events/create/{event_id}")
async def create_discord_events(
    event_id: str,
    guild_ids: List[str],
    create_channels: bool = True,
    create_signup_message: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """Create Discord scheduled events for VerseLink event across multiple guilds"""
    try:
        # Verify event exists
        db = get_database()
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Check user permissions for event
        if event_doc["created_by"] != current_user.id:
            # Check if user is org admin
            org_doc = await db.organizations.find_one({"id": event_doc["org_id"]})
            if not org_doc or org_doc["owner_id"] != current_user.id:
                # Check if user is org member with admin rights
                member_doc = await db.org_members.find_one({
                    "org_id": event_doc["org_id"],
                    "user_id": current_user.id,
                    "role": {"$in": ["admin", "moderator"]}
                })
                if not member_doc:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions to manage this event's Discord integration"
                    )
        
        # Queue Discord event creation jobs
        await discord_service.queue_discord_event_creation(
            event_id=event_id,
            guild_ids=guild_ids,
            create_channels=create_channels,
            create_signup_message=create_signup_message
        )
        
        return {
            "message": "Discord events creation queued",
            "event_id": event_id,
            "guild_ids": guild_ids,
            "jobs_queued": len(guild_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue Discord events creation: {str(e)}"
        )

@router.put("/events/update/{event_id}")
async def update_discord_events(
    event_id: str,
    guild_ids: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Update Discord scheduled events for VerseLink event"""
    try:
        db = get_database()
        
        # Verify event exists
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # If no guild_ids specified, get all guilds with Discord events for this event
        if not guild_ids:
            discord_events = []
            async for discord_event_doc in db.discord_events.find({"verselink_event_id": event_id}):
                discord_events.append(discord_event_doc["guild_id"])
            guild_ids = discord_events
        
        if not guild_ids:
            return {
                "message": "No Discord events found to update",
                "event_id": event_id
            }
        
        # Queue update jobs
        await discord_service.queue_discord_event_update(event_id, guild_ids)
        
        return {
            "message": "Discord events update queued",
            "event_id": event_id,
            "guild_ids": guild_ids,
            "jobs_queued": len(guild_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue Discord events update: {str(e)}"
        )

@router.delete("/events/delete/{event_id}")
async def delete_discord_events(
    event_id: str,
    guild_ids: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Delete Discord scheduled events for VerseLink event"""
    try:
        db = get_database()
        
        # If no guild_ids specified, get all guilds with Discord events for this event
        if not guild_ids:
            discord_events = []
            async for discord_event_doc in db.discord_events.find({"verselink_event_id": event_id}):
                discord_events.append(discord_event_doc["guild_id"])
            guild_ids = discord_events
        
        if not guild_ids:
            return {
                "message": "No Discord events found to delete",
                "event_id": event_id
            }
        
        # Queue deletion jobs
        await discord_service.queue_discord_event_deletion(event_id, guild_ids)
        
        return {
            "message": "Discord events deletion queued",
            "event_id": event_id,
            "guild_ids": guild_ids,
            "jobs_queued": len(guild_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue Discord events deletion: {str(e)}"
        )

@router.get("/events/{event_id}/discord", response_model=List[DiscordEventResponse])
async def get_discord_events_for_event(
    event_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get all Discord scheduled events for a VerseLink event"""
    try:
        db = get_database()
        
        discord_events = []
        async for discord_event_doc in db.discord_events.find({"verselink_event_id": event_id}):
            discord_events.append(DiscordEventResponse(
                id=discord_event_doc["id"],
                discord_event_id=discord_event_doc["discord_event_id"],
                guild_id=discord_event_doc["guild_id"],
                verselink_event_id=discord_event_doc["verselink_event_id"],
                name=discord_event_doc["name"],
                description=discord_event_doc.get("description"),
                status=discord_event_doc["status"],
                scheduled_start_time=discord_event_doc["scheduled_start_time"],
                scheduled_end_time=discord_event_doc.get("scheduled_end_time"),
                user_count=discord_event_doc.get("user_count", 0),
                created_at=discord_event_doc["created_at"]
            ))
        
        return discord_events
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Discord events: {str(e)}"
        )

@router.post("/events/{event_id}/signup-message")
async def create_signup_message(
    event_id: str,
    guild_id: str,
    channel_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Create interactive signup message for event"""
    try:
        # Verify event exists
        db = get_database()
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Create signup message
        interactive_message = await discord_events_service.create_signup_message(
            event_id=event_id,
            guild_id=guild_id,
            channel_id=channel_id
        )
        
        return {
            "message": "Signup message created",
            "interactive_message_id": interactive_message.id,
            "discord_message_id": interactive_message.discord_message_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create signup message: {str(e)}"
        )

@router.post("/events/{event_id}/sync-attendees")
async def sync_event_attendees(
    event_id: str,
    guild_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Sync attendees between VerseLink and Discord event"""
    try:
        result = await discord_events_service.sync_event_attendees(event_id, guild_id)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync attendees: {str(e)}"
        )

# Discord Interactions Handler
@router.post("/interactions")
async def handle_discord_interaction(request: Request):
    """Handle Discord interactions (buttons, select menus, slash commands)"""
    try:
        # Get raw body
        body = await request.body()
        
        # Verify Discord signature (if configured)
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")
        
        # Parse interaction data
        try:
            interaction_data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Handle ping (Discord verification)
        if interaction_data.get("type") == 1:  # PING
            return {"type": 1}  # PONG
        
        # Process interaction
        response = await discord_service.process_discord_interaction(interaction_data)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interaction processing failed: {str(e)}"
        )

# Event Management Integration
@router.post("/auto-manage/{event_id}")
async def auto_manage_event_discord(
    event_id: str,
    action: str,  # created, updated, cancelled, completed
    current_user: User = Depends(get_current_active_user)
):
    """Auto-manage Discord integration for event lifecycle"""
    try:
        db = get_database()
        
        # Get event and organization
        event_doc = await db.events.find_one({"id": event_id})
        if not event_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Get associated Discord guilds for the organization
        guild_ids = []
        async for guild_doc in db.discord_guilds.find({
            "org_id": event_doc["org_id"],
            "status": "active"
        }):
            guild_ids.append(guild_doc["guild_id"])
        
        if not guild_ids:
            return {
                "message": "No Discord guilds found for this organization",
                "event_id": event_id
            }
        
        # Handle different actions
        jobs_queued = 0
        
        if action == "created":
            await discord_service.queue_discord_event_creation(
                event_id=event_id,
                guild_ids=guild_ids,
                create_channels=True,
                create_signup_message=True
            )
            jobs_queued = len(guild_ids)
            
        elif action == "updated":
            await discord_service.queue_discord_event_update(event_id, guild_ids)
            jobs_queued = len(guild_ids)
            
        elif action in ["cancelled", "completed"]:
            await discord_service.queue_discord_event_update(event_id, guild_ids)
            jobs_queued = len(guild_ids)
            
            # If completed, also schedule cleanup
            if action == "completed":
                # Queue channel cleanup for tomorrow
                cleanup_time = datetime.utcnow() + timedelta(days=1)
                for guild_id in guild_ids:
                    cleanup_job = DiscordJobCreate(
                        job_type=JobType.CREATE_CHANNELS,  # Will be used for cleanup too
                        guild_id=guild_id,
                        event_id=event_id,
                        scheduled_at=cleanup_time,
                        payload={
                            "action": "cleanup",
                            "event_id": event_id
                        }
                    )
                    await discord_service.queue_job(cleanup_job)
                    jobs_queued += 1
        
        return {
            "message": f"Discord integration auto-management for '{action}' queued",
            "event_id": event_id,
            "action": action,
            "guild_ids": guild_ids,
            "jobs_queued": jobs_queued
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-management failed: {str(e)}"
        )

# Statistics
@router.get("/stats/events")
async def get_discord_events_stats(
    admin_user: User = Depends(require_site_admin)
):
    """Get Discord events integration statistics"""
    try:
        db = get_database()
        
        stats = {}
        
        # Discord events statistics
        stats["total_discord_events"] = await db.discord_events.count_documents({})
        stats["active_discord_events"] = await db.discord_events.count_documents({
            "status": {"$in": ["1", "2"]}  # SCHEDULED, ACTIVE
        })
        stats["completed_discord_events"] = await db.discord_events.count_documents({
            "status": "3"  # COMPLETED
        })
        
        # Interactive messages statistics
        stats["total_interactive_messages"] = await db.interactive_messages.count_documents({})
        stats["active_interactive_messages"] = await db.interactive_messages.count_documents({
            "active": True
        })
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        stats["recent_discord_events"] = await db.discord_events.count_documents({
            "created_at": {"$gte": yesterday}
        })
        stats["recent_interactions"] = await db.interactive_messages.count_documents({
            "created_at": {"$gte": yesterday}
        })
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

# Health Check
@router.get("/health")
async def discord_events_health():
    """Health check for Discord events integration"""
    try:
        db = get_database()
        
        # Check if we can query the database
        discord_events_count = await db.discord_events.count_documents({})
        
        return {
            "status": "healthy",
            "discord_events_count": discord_events_count,
            "bot_token_configured": bool(discord_events_service.bot_token),
            "message": "Discord events integration operational"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Discord events integration experiencing issues"
        }