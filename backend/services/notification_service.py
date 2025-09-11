from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from database import get_database
from models.notification import (
    Notification, NotificationCreate, NotificationType, NotificationPriority,
    NotificationPreference, NotificationPreferenceType
)
from models.user import User
import asyncio

class NotificationService:
    def __init__(self):
        self.db = get_database()
    
    async def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Create a new notification"""
        notification = Notification(**notification_data.dict())
        
        # Set expiration for certain types
        if notification.type in [NotificationType.EVENT_REMINDER, NotificationType.MAINTENANCE]:
            notification.expires_at = datetime.utcnow() + timedelta(days=7)
        
        await self.db.notifications.insert_one(notification.dict())
        return notification
    
    async def create_notification_for_user(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Dict[str, Any] = None,
        action_url: str = None
    ) -> Notification:
        """Create notification for a specific user"""
        notification_data = NotificationCreate(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            priority=priority,
            data=data or {},
            action_url=action_url
        )
        
        return await self.create_notification(notification_data)
    
    async def create_notification_for_multiple_users(
        self,
        user_ids: List[str],
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Dict[str, Any] = None,
        action_url: str = None
    ) -> List[Notification]:
        """Create notification for multiple users"""
        notifications = []
        
        for user_id in user_ids:
            notification = await self.create_notification_for_user(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                priority=priority,
                data=data,
                action_url=action_url
            )
            notifications.append(notification)
        
        return notifications
    
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 20,
        skip: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = {"user_id": user_id}
        
        if unread_only:
            query["read_at"] = None
        
        # Filter out expired notifications
        query["$or"] = [
            {"expires_at": None},
            {"expires_at": {"$gt": datetime.utcnow()}}
        ]
        
        cursor = self.db.notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
        notifications = []
        
        async for notification_doc in cursor:
            notifications.append(Notification(**notification_doc))
        
        return notifications
    
    async def mark_notification_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        result = await self.db.notifications.update_one(
            {"id": notification_id, "user_id": user_id, "read_at": None},
            {"$set": {"read_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    async def mark_all_notifications_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        result = await self.db.notifications.update_many(
            {"user_id": user_id, "read_at": None},
            {"$set": {"read_at": datetime.utcnow()}}
        )
        
        return result.modified_count
    
    async def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "$or": [
                    {"expires_at": None},
                    {"expires_at": {"$gt": datetime.utcnow()}}
                ]
            }},
            {"$group": {
                "_id": None,
                "total_count": {"$sum": 1},
                "unread_count": {"$sum": {"$cond": [{"$eq": ["$read_at", None]}, 1, 0]}},
                "by_type": {"$push": "$type"},
                "by_priority": {"$push": "$priority"}
            }}
        ]
        
        result = None
        async for doc in self.db.notifications.aggregate(pipeline):
            result = doc
            break
        
        if not result:
            return {
                "total_count": 0,
                "unread_count": 0,
                "by_type": {},
                "by_priority": {}
            }
        
        # Count occurrences
        type_counts = {}
        for type_val in result["by_type"]:
            type_counts[type_val] = type_counts.get(type_val, 0) + 1
        
        priority_counts = {}
        for priority_val in result["by_priority"]:
            priority_counts[priority_val] = priority_counts.get(priority_val, 0) + 1
        
        return {
            "total_count": result["total_count"],
            "unread_count": result["unread_count"],
            "by_type": type_counts,
            "by_priority": priority_counts
        }
    
    async def delete_old_notifications(self, days_old: int = 30) -> int:
        """Delete old read notifications"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await self.db.notifications.delete_many({
            "read_at": {"$lt": cutoff_date}
        })
        
        return result.deleted_count
    
    async def delete_expired_notifications(self) -> int:
        """Delete expired notifications"""
        result = await self.db.notifications.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        
        return result.deleted_count
    
    # Event-related notifications
    async def notify_event_created(self, event_id: str, org_id: str, event_title: str):
        """Notify org members about new event"""
        # Get org members
        members = []
        async for member_doc in self.db.org_members.find({"org_id": org_id}):
            members.append(member_doc["user_id"])
        
        if members:
            await self.create_notification_for_multiple_users(
                user_ids=members,
                type=NotificationType.ORG_EVENT_PUBLISHED,
                title="Nouvel événement publié",
                message=f"L'événement '{event_title}' a été publié dans votre organisation.",
                data={"event_id": event_id, "org_id": org_id},
                action_url=f"/events/{event_id}"
            )
    
    async def notify_event_signup_confirmed(self, user_id: str, event_id: str, event_title: str):
        """Notify user their event signup is confirmed"""
        await self.create_notification_for_user(
            user_id=user_id,
            type=NotificationType.EVENT_SIGNUP_CONFIRMED,
            title="Inscription confirmée",
            message=f"Votre inscription pour '{event_title}' a été confirmée !",
            priority=NotificationPriority.HIGH,
            data={"event_id": event_id},
            action_url=f"/events/{event_id}"
        )
    
    async def notify_event_reminder(self, user_id: str, event_id: str, event_title: str, time_until: str):
        """Send event reminder notification"""
        await self.create_notification_for_user(
            user_id=user_id,
            type=NotificationType.EVENT_REMINDER,
            title="Rappel d'événement",
            message=f"L'événement '{event_title}' commence dans {time_until}.",
            priority=NotificationPriority.HIGH,
            data={"event_id": event_id},
            action_url=f"/events/{event_id}"
        )
    
    # Tournament-related notifications
    async def notify_tournament_created(self, tournament_id: str, org_id: str, tournament_name: str):
        """Notify org members about new tournament"""
        # Get org members
        members = []
        async for member_doc in self.db.org_members.find({"org_id": org_id}):
            members.append(member_doc["user_id"])
        
        if members:
            await self.create_notification_for_multiple_users(
                user_ids=members,
                type=NotificationType.TOURNAMENT_CREATED,
                title="Nouveau tournoi créé",
                message=f"Le tournoi '{tournament_name}' est maintenant ouvert aux inscriptions !",
                data={"tournament_id": tournament_id, "org_id": org_id},
                action_url=f"/tournaments/{tournament_id}"
            )
    
    async def notify_match_result(self, user_id: str, match_id: str, tournament_name: str, won: bool):
        """Notify user about match result"""
        title = "Victoire !" if won else "Défaite"
        message = f"Votre équipe a {'gagné' if won else 'perdu'} son match dans le tournoi '{tournament_name}'."
        
        await self.create_notification_for_user(
            user_id=user_id,
            type=NotificationType.MATCH_RESULT,
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            data={"match_id": match_id, "won": won},
            action_url=f"/tournaments/{tournament_name}#matches"
        )

    async def notify_match_disputed(self, tournament_id: str, match_id: str):
        """Notify tournament organizer and admins about a disputed match"""
        tournament_doc = await self.db.tournaments.find_one({"id": tournament_id})
        if not tournament_doc:
            return

        org_id = tournament_doc["org_id"]
        recipients = {tournament_doc["created_by"]}
        async for member_doc in self.db.org_members.find({"org_id": org_id, "role": {"$in": ["admin", "moderator"]}}):
            recipients.add(member_doc["user_id"])

        if recipients:
            await self.create_notification_for_multiple_users(
                user_ids=list(recipients),
                type=NotificationType.MATCH_DISPUTED,
                title="Match contesté",
                message=f"Un différend a été signalé pour un match du tournoi '{tournament_doc['name']}'.",
                priority=NotificationPriority.HIGH,
                data={"tournament_id": tournament_id, "match_id": match_id},
                action_url=f"/tournaments/{tournament_id}#matches"
            )
    
    # Organization notifications
    async def notify_org_member_joined(self, org_id: str, new_member_handle: str):
        """Notify org admins about new member"""
        # Get org admins
        admin_members = []
        async for member_doc in self.db.org_members.find({"org_id": org_id, "role": {"$in": ["admin", "moderator"]}}):
            admin_members.append(member_doc["user_id"])
        
        if admin_members:
            await self.create_notification_for_multiple_users(
                user_ids=admin_members,
                type=NotificationType.ORG_MEMBER_JOINED,
                title="Nouveau membre",
                message=f"{new_member_handle} a rejoint l'organisation.",
                data={"org_id": org_id, "new_member": new_member_handle}
            )
    
    # Moderation notifications
    async def notify_warning_received(self, user_id: str, reason: str):
        """Notify user about warning"""
        await self.create_notification_for_user(
            user_id=user_id,
            type=NotificationType.WARNING_RECEIVED,
            title="Avertissement reçu",
            message=f"Vous avez reçu un avertissement : {reason}",
            priority=NotificationPriority.HIGH,
            data={"reason": reason}
        )

    async def notify_match_score_reported(self, tournament_id: str, match_id: str, recipient_user_id: str):
        """Notify opposing team captain that a score has been proposed"""
        tournament_doc = await self.db.tournaments.find_one({"id": tournament_id})
        if not tournament_doc:
            return

        await self.create_notification_for_user(
            user_id=recipient_user_id,
            type=NotificationType.MATCH_SCORE_REPORTED,
            title="Score proposé",
            message=f"Votre adversaire a proposé un score pour le tournoi '{tournament_doc['name']}'.",
            priority=NotificationPriority.NORMAL,
            data={"tournament_id": tournament_id, "match_id": match_id},
            action_url=f"/tournaments/{tournament_id}#matches"
        )
    
    async def notify_strike_received(self, user_id: str, reason: str, strike_count: int):
        """Notify user about strike"""
        await self.create_notification_for_user(
            user_id=user_id,
            type=NotificationType.STRIKE_RECEIVED,
            title="Strike reçu",
            message=f"Vous avez reçu un strike ({strike_count}/5) : {reason}",
            priority=NotificationPriority.URGENT,
            data={"reason": reason, "strike_count": strike_count}
        )
    
    async def notify_reputation_changed(self, user_id: str, old_reputation: int, new_reputation: int):
        """Notify user about reputation change"""
        change = new_reputation - old_reputation
        direction = "augmenté" if change > 0 else "diminué"
        
        await self.create_notification_for_user(
            user_id=user_id,
            type=NotificationType.REPUTATION_CHANGED,
            title="Réputation modifiée",
            message=f"Votre réputation a {direction} de {abs(change)} points (maintenant {new_reputation}).",
            priority=NotificationPriority.NORMAL if change > 0 else NotificationPriority.HIGH,
            data={"old_reputation": old_reputation, "new_reputation": new_reputation, "change": change}
        )
    
    # System notifications
    async def notify_welcome(self, user_id: str, user_handle: str):
        """Send welcome notification to new user"""
        await self.create_notification_for_user(
            user_id=user_id,
            type=NotificationType.WELCOME,
            title=f"Bienvenue sur VerseLink, {user_handle} !",
            message="Découvrez les événements et tournois Star Citizen organisés par la communauté.",
            priority=NotificationPriority.NORMAL,
            action_url="/events"
        )