from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from pydantic import BaseModel

from database import get_database
from models.user import User
from services.auto_moderation_service import AutoModerationService
from middleware.auth import get_current_active_user, require_site_admin

router = APIRouter()
auto_moderation_service = AutoModerationService()

class AutoModerationConfigUpdate(BaseModel):
    enabled: bool = None
    spam_detection: Dict[str, Any] = None
    profanity_filter: Dict[str, Any] = None
    harassment_detection: Dict[str, Any] = None
    excessive_reporting: Dict[str, Any] = None

class MessageCheckRequest(BaseModel):
    content: str
    context: str = None

@router.get("/config")
async def get_auto_moderation_config(current_user: User = Depends(require_site_admin)):
    """Get auto-moderation configuration (admin only)"""
    config = await auto_moderation_service.get_auto_moderation_config()
    return {"config": config}

@router.put("/config")
async def update_auto_moderation_config(
    config_update: AutoModerationConfigUpdate,
    current_user: User = Depends(require_site_admin)
):
    """Update auto-moderation configuration (admin only)"""
    # Convert to dict and remove None values
    update_data = {k: v for k, v in config_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No configuration changes provided"
        )
    
    updated_config = await auto_moderation_service.update_auto_moderation_config(update_data)
    return {
        "message": "Auto-moderation configuration updated successfully",
        "config": updated_config
    }

@router.post("/toggle")
async def toggle_auto_moderation(
    enabled: bool,
    current_user: User = Depends(require_site_admin)
):
    """Toggle auto-moderation on/off (admin only)"""
    result = await auto_moderation_service.toggle_auto_moderation(enabled)
    return {
        "message": f"Auto-moderation {'enabled' if result else 'disabled'}",
        "enabled": result
    }

@router.post("/check-message")
async def check_message_content(
    request: MessageCheckRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Check message content for violations (for testing purposes)"""
    result = await auto_moderation_service.check_message_content(
        user_id=current_user.id,
        content=request.content,
        context=request.context
    )
    
    if result:
        return {
            "violations_detected": True,
            "violations": result["violations"],
            "action_taken": result["action_taken"]
        }
    else:
        return {
            "violations_detected": False,
            "message": "No violations detected"
        }

@router.get("/stats")
async def get_auto_moderation_stats(current_user: User = Depends(require_site_admin)):
    """Get auto-moderation statistics (admin only)"""
    stats = await auto_moderation_service.get_auto_moderation_stats()
    return stats

@router.get("/logs")
async def get_auto_moderation_logs(
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(require_site_admin)
):
    """Get auto-moderation logs (admin only)"""
    db = get_database()
    
    cursor = db.auto_moderation_logs.find().sort("created_at", -1).skip(skip).limit(limit)
    logs = []
    
    async for log_doc in cursor:
        # Get user details
        user_doc = await db.users.find_one({"id": log_doc.get("user_id")})
        user_handle = user_doc["handle"] if user_doc else "Unknown"
        
        logs.append({
            "id": log_doc.get("id"),
            "type": log_doc.get("type"),
            "user_id": log_doc.get("user_id"),
            "user_handle": user_handle,
            "action": log_doc.get("action"),
            "reason": log_doc.get("reason"),
            "violations": log_doc.get("violations", []),
            "context": log_doc.get("context"),
            "created_at": log_doc.get("created_at")
        })
    
    return {"logs": logs}

@router.delete("/logs")
async def clear_old_auto_moderation_logs(
    days_old: int = 30,
    current_user: User = Depends(require_site_admin)
):
    """Clear old auto-moderation logs (admin only)"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    db = get_database()
    
    result = await db.auto_moderation_logs.delete_many({
        "created_at": {"$lt": cutoff_date}
    })
    
    return {
        "message": f"Deleted {result.deleted_count} old auto-moderation logs",
        "deleted_count": result.deleted_count
    }