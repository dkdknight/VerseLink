from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_database
from models.user import User
from models.notification import (
    Notification, NotificationResponse, NotificationStats,
    NotificationPreferenceUpdate
)
from services.notification_service import NotificationService
from middleware.auth import get_current_active_user

router = APIRouter()
notification_service = NotificationService()

def _calculate_time_ago(created_at: datetime) -> str:
    """Calculate human-readable time ago"""
    now = datetime.utcnow()
    diff = now - created_at
    
    if diff.days > 0:
        if diff.days == 1:
            return "il y a 1 jour"
        elif diff.days < 7:
            return f"il y a {diff.days} jours"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"il y a {weeks} semaine{'s' if weeks > 1 else ''}"
        else:
            months = diff.days // 30
            return f"il y a {months} mois"
    
    hours = diff.seconds // 3600
    if hours > 0:
        return f"il y a {hours}h"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"il y a {minutes}min"
    
    return "à l'instant"

@router.get("/me", response_model=List[NotificationResponse])
async def get_my_notifications(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's notifications"""
    notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        skip=skip,
        unread_only=unread_only
    )
    
    response = []
    for notification in notifications:
        response.append(NotificationResponse(
            **notification.dict(),
            is_read=notification.read_at is not None,
            time_ago=_calculate_time_ago(notification.created_at)
        ))
    
    return response

@router.get("/me/stats", response_model=NotificationStats)
async def get_my_notification_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get notification statistics for current user"""
    stats = await notification_service.get_notification_stats(current_user.id)
    return NotificationStats(**stats)

@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Mark a notification as read"""
    success = await notification_service.mark_notification_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or already read"
        )
    
    return {"message": "Notification marked as read"}

@router.post("/me/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_active_user)
):
    """Mark all notifications as read"""
    count = await notification_service.mark_all_notifications_as_read(current_user.id)
    return {"message": f"{count} notifications marked as read"}

@router.get("/me/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user)
):
    """Get user's notification preferences"""
    db = get_database()
    
    # Get all preferences for user
    preferences = {}
    async for pref_doc in db.notification_preferences.find({"user_id": current_user.id}):
        preferences[pref_doc["notification_type"]] = {
            "in_app_enabled": pref_doc["in_app_enabled"],
            "email_enabled": pref_doc["email_enabled"],
            "discord_dm_enabled": pref_doc["discord_dm_enabled"]
        }
    
    # Fill in defaults for missing preferences
    from models.notification import NotificationType
    default_preferences = {
        NotificationType.EVENT_CREATED: {"in_app_enabled": True, "email_enabled": False, "discord_dm_enabled": False},
        NotificationType.EVENT_REMINDER: {"in_app_enabled": True, "email_enabled": True, "discord_dm_enabled": False},
        NotificationType.EVENT_SIGNUP_CONFIRMED: {"in_app_enabled": True, "email_enabled": True, "discord_dm_enabled": False},
        NotificationType.TOURNAMENT_CREATED: {"in_app_enabled": True, "email_enabled": False, "discord_dm_enabled": False},
        NotificationType.MATCH_RESULT: {"in_app_enabled": True, "email_enabled": True, "discord_dm_enabled": False},
        NotificationType.EVENT_CHAT_MESSAGE: {"in_app_enabled": True, "email_enabled": False, "discord_dm_enabled": True},
        NotificationType.MATCH_CHAT_MESSAGE: {"in_app_enabled": True, "email_enabled": False, "discord_dm_enabled": True},
        NotificationType.ORG_MEMBER_JOINED: {"in_app_enabled": True, "email_enabled": False, "discord_dm_enabled": False},
        NotificationType.WARNING_RECEIVED: {"in_app_enabled": True, "email_enabled": True, "discord_dm_enabled": False},
        NotificationType.STRIKE_RECEIVED: {"in_app_enabled": True, "email_enabled": True, "discord_dm_enabled": False},
        NotificationType.REPUTATION_CHANGED: {"in_app_enabled": True, "email_enabled": False, "discord_dm_enabled": False},
        NotificationType.WELCOME: {"in_app_enabled": True, "email_enabled": False, "discord_dm_enabled": False},
    }
    
    for notif_type, default_prefs in default_preferences.items():
        if notif_type not in preferences:
            preferences[notif_type] = default_prefs
    
    return {"preferences": preferences}

@router.put("/me/preferences")
async def update_notification_preferences(
    preferences_update: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update user's notification preferences"""
    db = get_database()
    
    from models.notification import NotificationPreference, NotificationType
    
    # Update each preference
    for notif_type_str, prefs in preferences_update.preferences.items():
        try:
            notif_type = NotificationType(notif_type_str)
        except ValueError:
            continue  # Skip invalid notification types
        
        # Upsert preference
        await db.notification_preferences.update_one(
            {"user_id": current_user.id, "notification_type": notif_type},
            {
                "$set": {
                    "in_app_enabled": prefs.get("in_app_enabled", True),
                    "email_enabled": prefs.get("email_enabled", False),
                    "discord_dm_enabled": prefs.get("discord_dm_enabled", False),
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    return {"message": "Notification preferences updated"}

# Utility endpoint for testing notifications (development only)
@router.post("/test")
async def create_test_notification(
    current_user: User = Depends(get_current_active_user)
):
    """Create a test notification (development only)"""
    from models.notification import NotificationType, NotificationPriority
    
    await notification_service.create_notification_for_user(
        user_id=current_user.id,
        type=NotificationType.SYSTEM_UPDATE,
        title="Test de notification",
        message="Ceci est une notification de test pour vérifier le système.",
        priority=NotificationPriority.NORMAL,
        data={"test": True},
        action_url="/profile"
    )
    
    return {"message": "Test notification created"}