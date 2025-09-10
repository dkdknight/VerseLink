from typing import List
from fastapi import HTTPException
from database import get_database
from models.chat import ChatMessage, ChatContext
from models.notification import NotificationType
from services.notification_service import NotificationService
from services.discord_service import DiscordService
from models.user import User
from datetime import datetime

class ChatService:
    def __init__(self):
        self.db = get_database()
        self.notification_service = NotificationService()
        self.discord_service = DiscordService()

    async def _get_user(self, user_id: str) -> User | None:
        user_doc = await self.db.users.find_one({"id": user_id})
        return User(**user_doc) if user_doc else None

    async def _is_event_participant(self, event_id: str, user_id: str) -> bool:
        if await self.db.event_signups.find_one({"event_id": event_id, "user_id": user_id}):
            return True
        event_doc = await self.db.events.find_one({"id": event_id})
        if not event_doc:
            return False
        return event_doc.get("created_by") == user_id

    async def _is_match_captain(self, match_id: str, user_id: str) -> bool:
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            return False
        return user_id in [match_doc.get("team_a_captain_id"), match_doc.get("team_b_captain_id")]

    async def get_messages(self, context: ChatContext, context_id: str, limit: int = 50) -> List[ChatMessage]:
        cursor = self.db.chat_messages.find({"context": context, "context_id": context_id}).sort("created_at", 1).limit(limit)
        messages = []
        async for doc in cursor:
            messages.append(ChatMessage(**doc))
        return messages

    async def create_event_message(self, event_id: str, user: User, content: str) -> ChatMessage:
        if not await self._is_event_participant(event_id, user.id):
            raise HTTPException(status_code=403, detail="Not allowed")
        message = ChatMessage(context=ChatContext.EVENT, context_id=event_id, sender_id=user.id, sender_handle=user.handle, content=content)
        await self.db.chat_messages.insert_one(message.dict())
        recipients = []
        async for signup in self.db.event_signups.find({"event_id": event_id}):
            if signup["user_id"] != user.id:
                recipients.append(signup["user_id"])
        event_doc = await self.db.events.find_one({"id": event_id})
        if event_doc and event_doc.get("created_by") not in recipients and event_doc.get("created_by") != user.id:
            recipients.append(event_doc.get("created_by"))
        if recipients:
            title = "Nouveau message dans l'événement"
            body = f"{user.handle}: {content}"
            await self.notification_service.create_notification_for_multiple_users(
                recipients,
                NotificationType.EVENT_CHAT_MESSAGE,
                title,
                body,
                data={"event_id": event_id}
            )
            for rid in recipients:
                ruser = await self._get_user(rid)
                if ruser and ruser.dm_opt_in and ruser.discord_id:
                    await self.discord_service.send_dm(ruser.discord_id, body)
        return message

    async def create_match_message(self, match_id: str, user: User, content: str) -> ChatMessage:
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            raise HTTPException(status_code=404, detail="Match not found")
        if user.id not in [match_doc.get("team_a_captain_id"), match_doc.get("team_b_captain_id")]:
            raise HTTPException(status_code=403, detail="Not allowed")
        message = ChatMessage(context=ChatContext.MATCH, context_id=match_id, sender_id=user.id, sender_handle=user.handle, content=content)
        await self.db.chat_messages.insert_one(message.dict())
        other_id = match_doc.get("team_a_captain_id") if user.id == match_doc.get("team_b_captain_id") else match_doc.get("team_b_captain_id")
        if other_id:
            title = "Message privé de match"
            body = f"{user.handle}: {content}"
            await self.notification_service.create_notification_for_user(
                other_id,
                NotificationType.MATCH_CHAT_MESSAGE,
                title,
                body,
                data={"match_id": match_id}
            )
            ruser = await self._get_user(other_id)
            if ruser and ruser.dm_opt_in and ruser.discord_id:
                await self.discord_service.send_dm(ruser.discord_id, body)
        return message