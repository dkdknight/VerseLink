import httpx
import asyncio
import hmac
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decouple import config

from database import get_database
from models.discord_integration import (
    DiscordGuild, DiscordGuildCreate, DiscordJob, DiscordJobCreate,
    WebhookLog, WebhookType, WebhookEvent, JobType, JobStatus,
    SyncedMessage, ReminderType, BotAuthToken
)
from models.event import Event
from models.tournament import Tournament
from services.notification_service import NotificationService

class DiscordService:
    """Service for managing Discord integrations, webhooks, and bot communication"""
    
    def __init__(self):
        self.db = get_database()
        self.notification_service = NotificationService()
        self.webhook_secret = config("DISCORD_BOT_WEBHOOK_SECRET", default="")
        self.bot_api_base_url = config("DISCORD_BOT_API_URL", default="")
        self.bot_api_token = config("DISCORD_BOT_API_TOKEN", default="")
        
    # Guild Management
    async def register_guild(self, guild_data: DiscordGuildCreate, org_id: Optional[str] = None) -> DiscordGuild:
        """Register a new Discord guild"""
        # Check if guild already exists
        existing_guild = await self.db.discord_guilds.find_one({"guild_id": guild_data.guild_id})
        if existing_guild:
            # Auto-link existing guild if no organization is set and one is provided
            if org_id and not existing_guild.get("org_id"):
                await self.db.discord_guilds.update_one(
                    {"guild_id": guild_data.guild_id},
                    {"$set": {"org_id": org_id, "updated_at": datetime.utcnow()}}
                )
                await self.db.organizations.update_one(
                    {"id": org_id},
                    {"$set": {"discord_guild_id": guild_data.guild_id, "updated_at": datetime.utcnow()}}
                )
                linked_guild = await self.db.discord_guilds.find_one({"guild_id": guild_data.guild_id})
                return DiscordGuild(**linked_guild)
            raise ValueError("Guild already registered")
        
        guild = DiscordGuild(**guild_data.dict(), org_id=org_id)
        await self.db.discord_guilds.insert_one(guild.dict())

        # Link organization if provided
        if org_id:
            await self.db.organizations.update_one(
                {"id": org_id},
                {"$set": {"discord_guild_id": guild.guild_id, "updated_at": datetime.utcnow()}}
            )
        
        # Create default reminder configurations
        await self._create_default_reminder_configs(guild.id)
        
        return guild
    
    async def get_guild(self, guild_id: str) -> Optional[DiscordGuild]:
        """Get Discord guild by ID"""
        guild_doc = await self.db.discord_guilds.find_one({"guild_id": guild_id})
        return DiscordGuild(**guild_doc) if guild_doc else None
    
    async def get_guild_by_org(self, org_id: str) -> List[DiscordGuild]:
        """Get all Discord guilds for an organization"""
        guilds = []
        async for guild_doc in self.db.discord_guilds.find({"org_id": org_id}):
            guilds.append(DiscordGuild(**guild_doc))
        return guilds
    
    async def update_guild_webhook_status(self, guild_id: str, verified: bool) -> bool:
        """Update webhook verification status for a guild"""
        result = await self.db.discord_guilds.update_one(
            {"guild_id": guild_id},
            {"$set": {"webhook_verified": verified, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    # Webhook Management
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Discord webhook HMAC signature"""
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    async def log_webhook(self, webhook_data: Dict[str, Any], webhook_type: WebhookType, 
                         event_type: WebhookEvent, response_code: Optional[int] = None,
                         error_message: Optional[str] = None) -> WebhookLog:
        """Log webhook activity"""
        webhook_log = WebhookLog(
            webhook_type=webhook_type,
            event_type=event_type,
            guild_id=webhook_data.get("guild_id"),
            payload=webhook_data,
            response_code=response_code,
            error_message=error_message
        )
        
        await self.db.webhook_logs.insert_one(webhook_log.dict())
        return webhook_log
    
    async def process_incoming_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook from Discord"""
        event_type = webhook_data.get("event_type")
        guild_id = webhook_data.get("guild_id")
        
        # Log the webhook
        await self.log_webhook(webhook_data, WebhookType.INCOMING, WebhookEvent(event_type))
        
        # Process based on event type
        if event_type == WebhookEvent.GUILD_MEMBER_ADD:
            return await self._handle_member_add(webhook_data)
        elif event_type == WebhookEvent.MESSAGE_CREATE:
            return await self._handle_message_sync(webhook_data)
        elif event_type == WebhookEvent.GUILD_MEMBER_REMOVE:
            return await self._handle_member_remove(webhook_data)
        else:
            return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}
    
    # Job Queue System
    async def queue_job(self, job_data: DiscordJobCreate) -> DiscordJob:
        """Queue a Discord job for processing"""
        job = DiscordJob(**job_data.dict())
        await self.db.discord_jobs.insert_one(job.dict())
        return job
    
    async def get_pending_jobs(self, limit: int = 10) -> List[DiscordJob]:
        """Get pending jobs for processing"""
        jobs = []
        async for job_doc in self.db.discord_jobs.find({
            "status": JobStatus.PENDING,
            "scheduled_at": {"$lte": datetime.utcnow()}
        }).limit(limit):
            jobs.append(DiscordJob(**job_doc))
        return jobs
    
    async def update_job_status(self, job_id: str, status: JobStatus, 
                               result: Optional[Dict[str, Any]] = None,
                               error_message: Optional[str] = None) -> bool:
        """Update job status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if result:
            update_data["result"] = result
        if error_message:
            update_data["error_message"] = error_message
        if status == JobStatus.PROCESSING:
            update_data["started_at"] = datetime.utcnow()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            update_data["completed_at"] = datetime.utcnow()
        
        result = await self.db.discord_jobs.update_one(
            {"id": job_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def process_jobs(self):
        """Process pending Discord jobs (should be called by scheduler)"""
        jobs = await self.get_pending_jobs()
        
        for job in jobs:
            try:
                await self.update_job_status(job.id, JobStatus.PROCESSING)
                
                if job.job_type == JobType.REMINDER:
                    result = await self._process_reminder_job(job)
                elif job.job_type == JobType.ANNOUNCEMENT:
                    result = await self._process_announcement_job(job)
                elif job.job_type == JobType.SYNC_MESSAGE:
                    result = await self._process_sync_message_job(job)
                elif job.job_type == JobType.WEBHOOK_DELIVERY:
                    result = await self._process_webhook_delivery_job(job)
                elif job.job_type in [JobType.CREATE_DISCORD_EVENT, JobType.UPDATE_DISCORD_EVENT, JobType.DELETE_DISCORD_EVENT]:
                    # Delegate to Discord Events Service
                    from services.discord_events_service import DiscordEventsService
                    events_service = DiscordEventsService()
                    await events_service.process_discord_event_jobs()
                    result = {"delegated": "discord_events_service"}
                elif job.job_type == JobType.CREATE_CHANNELS:
                    result = await self._process_create_channels_job(job)
                elif job.job_type == JobType.MANAGE_ROLES:
                    result = await self._process_manage_roles_job(job)
                elif job.job_type == JobType.SYNC_REACTIONS:
                    result = await self._process_sync_reactions_job(job)
                else:
                    raise ValueError(f"Unknown job type: {job.job_type}")
                
                await self.update_job_status(job.id, JobStatus.COMPLETED, result=result)
                
            except Exception as e:
                error_msg = str(e)
                job.retry_count += 1
                
                if job.retry_count >= job.max_retries:
                    await self.update_job_status(job.id, JobStatus.FAILED, error_message=error_msg)
                else:
                    # Reschedule with exponential backoff
                    retry_delay = 2 ** job.retry_count * 60  # Minutes
                    scheduled_at = datetime.utcnow() + timedelta(minutes=retry_delay)
                    
                    await self.db.discord_jobs.update_one(
                        {"id": job.id},
                        {"$set": {
                            "status": JobStatus.PENDING,
                            "retry_count": job.retry_count,
                            "scheduled_at": scheduled_at,
                            "error_message": error_msg,
                            "updated_at": datetime.utcnow()
                        }}
                    )
    
    # Event and Tournament Announcements
    async def announce_event(self, event_id: str, announcement_type: str, guild_ids: List[str]):
        """Queue event announcement to Discord guilds"""
        # Get event details
        event_doc = await self.db.events.find_one({"id": event_id})
        if not event_doc:
            raise ValueError("Event not found")
        
        event = Event(**event_doc)
        
        for guild_id in guild_ids:
            job_data = DiscordJobCreate(
                job_type=JobType.ANNOUNCEMENT,
                guild_id=guild_id,
                event_id=event_id,
                payload={
                    "type": "event",
                    "action": announcement_type,
                    "event": event.dict()
                }
            )
            await self.queue_job(job_data)
    
    async def announce_tournament(self, tournament_id: str, announcement_type: str, guild_ids: List[str]):
        """Queue tournament announcement to Discord guilds"""
        # Get tournament details
        tournament_doc = await self.db.tournaments.find_one({"id": tournament_id})
        if not tournament_doc:
            raise ValueError("Tournament not found")
        
        tournament = Tournament(**tournament_doc)
        
        for guild_id in guild_ids:
            job_data = DiscordJobCreate(
                job_type=JobType.ANNOUNCEMENT,
                guild_id=guild_id,
                event_id=tournament_id,
                payload={
                    "type": "tournament",
                    "action": announcement_type,
                    "tournament": tournament.dict()
                }
            )
            await self.queue_job(job_data)
    
    # Reminder System
    async def schedule_event_reminders(self, event_id: str):
        """Schedule automatic reminders for an event"""
        event_doc = await self.db.events.find_one({"id": event_id})
        if not event_doc:
            return
        
        event = Event(**event_doc)
        
        # Get guilds for the event's organization
        guilds = await self.get_guild_by_org(event.org_id)
        
        for guild in guilds:
            if not guild.reminder_enabled:
                continue
            
            # Get reminder configurations for this guild
            reminder_configs = []
            async for config_doc in self.db.reminder_configs.find({"guild_id": guild.guild_id, "enabled": True}):
                reminder_configs.append(config_doc)
            
            for config in reminder_configs:
                reminder_time = self._calculate_reminder_time(event.start_at_utc, config["reminder_type"], config.get("offset_minutes", 0))
                
                if reminder_time > datetime.utcnow():
                    job_data = DiscordJobCreate(
                        job_type=JobType.REMINDER,
                        guild_id=guild.guild_id,
                        event_id=event_id,
                        scheduled_at=reminder_time,
                        payload={
                            "reminder_type": config["reminder_type"],
                            "event": event.dict(),
                            "custom_message": config.get("custom_message"),
                            "channel_id": config.get("channel_id")
                        }
                    )
                    await self.queue_job(job_data)
    
    def _calculate_reminder_time(self, event_time: datetime, reminder_type: str, offset_minutes: int = 0) -> datetime:
        """Calculate when to send a reminder"""
        if reminder_type == ReminderType.EVENT_J3:
            return event_time - timedelta(days=3)
        elif reminder_type == ReminderType.EVENT_J1:
            return event_time - timedelta(days=1)
        elif reminder_type == ReminderType.EVENT_H1:
            return event_time - timedelta(hours=1)
        elif reminder_type == ReminderType.CUSTOM:
            return event_time - timedelta(minutes=offset_minutes)
        else:
            return event_time - timedelta(hours=1)  # Default
    
    # Message Synchronization
    async def sync_message(self, source_guild_id: str, target_guild_ids: List[str], 
                          message_content: str, author_name: str, channel_type: str = "announcement"):
        """Synchronize message across multiple Discord guilds"""
        synced_message = SyncedMessage(
            original_guild_id=source_guild_id,
            original_channel_id="", # Will be filled by the webhook
            original_message_id="", # Will be filled by the webhook
            content=message_content,
            author_id="", # Will be filled by the webhook
            author_name=author_name,
            message_type=channel_type
        )
        
        await self.db.synced_messages.insert_one(synced_message.dict())
        
        # Queue sync jobs for each target guild
        for target_guild_id in target_guild_ids:
            if target_guild_id != source_guild_id:  # Don't sync back to source
                job_data = DiscordJobCreate(
                    job_type=JobType.SYNC_MESSAGE,
                    guild_id=target_guild_id,
                    payload={
                        "synced_message_id": synced_message.id,
                        "content": message_content,
                        "author_name": author_name,
                        "channel_type": channel_type,
                        "source_guild_id": source_guild_id
                    }
                )
                await self.queue_job(job_data)
    
    # Bot API Communication
    async def call_bot_api(self, endpoint: str, method: str = "POST", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API call to Discord bot"""
        if not self.bot_api_base_url or not self.bot_api_token:
            raise ValueError("Bot API configuration missing")
        
        url = f"{self.bot_api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.bot_api_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers)
                return {
                    "status_code": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
            elif method.upper() == "GET":
                response = await client.get(url, headers=headers)
                return {
                    "status_code": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }

    async def send_dm(self, discord_id: str, message: str):
        """Send direct message via bot"""
        if not self.bot_api_base_url or not self.bot_api_token:
            return
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.bot_api_base_url.rstrip('/')}/dm",
                    json={"discord_id": discord_id, "message": message},
                    headers={"Authorization": f"Bearer {self.bot_api_token}"},
                    timeout=10,
                )
        except Exception:
            pass
    
    # Authentication for Bot API
    async def verify_bot_auth(self, guild_id: str, api_key: str) -> bool:
        """Verify bot API authentication"""
        guild = await self.get_guild(guild_id)
        return guild and guild.api_key == api_key
    
    # Private methods for job processing
    async def _process_reminder_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process reminder job"""
        payload = job.payload
        reminder_data = {
            "guild_id": job.guild_id,
            "event_id": job.event_id,
            "reminder_type": payload["reminder_type"],
            "event": payload["event"],
            "custom_message": payload.get("custom_message"),
            "channel_id": payload.get("channel_id")
        }
        
        return await self.call_bot_api("reminders/send", data=reminder_data)
    
    async def _process_announcement_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process announcement job"""
        payload = job.payload
        announcement_data = {
            "guild_id": job.guild_id,
            "type": payload["type"],
            "action": payload["action"],
            # Ensure required fields for the bot API
            "data": payload.get("data") or {},
        }
        
        if payload["type"] == "event":
            announcement_data["event"] = payload["event"]
            event_info = payload["event"]
            slug = event_info.get("slug") or event_info.get("id")
            announcement_data["url"] = payload.get("url") or f"/events/{slug}"
        elif payload["type"] == "tournament":
            announcement_data["tournament"] = payload["tournament"]
            tournament_info = payload["tournament"]
            slug = tournament_info.get("slug") or tournament_info.get("id")
            announcement_data["url"] = payload.get("url") or f"/tournaments/{slug}"
        
        return await self.call_bot_api("announcements/send", data=announcement_data)
    
    async def _process_sync_message_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process message sync job"""
        payload = job.payload
        sync_data = {
            "guild_id": job.guild_id,
            "content": payload["content"],
            "author_name": payload["author_name"],
            "channel_type": payload["channel_type"],
            "source_guild_id": payload["source_guild_id"]
        }
        
        return await self.call_bot_api("messages/sync", data=sync_data)
    
    async def _process_webhook_delivery_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process webhook delivery job"""
        payload = job.payload
        return await self.call_bot_api("webhooks/deliver", data=payload)
    
    async def _handle_member_add(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Discord member join event"""
        guild_id = webhook_data.get("guild_id")
        user_data = webhook_data.get("user", {})
        discord_id = user_data.get("id")
        
        if discord_id:
            # Check if user exists in our system
            user_doc = await self.db.users.find_one({"discord_id": discord_id})
            if user_doc:
                # Update last seen
                await self.db.users.update_one(
                    {"discord_id": discord_id},
                    {"$set": {"last_seen_at": datetime.utcnow()}}
                )
                
                # Send welcome notification if enabled
                await self.notification_service.notify_welcome(user_doc["id"], user_doc["handle"])
        
        return {"status": "processed", "action": "member_add"}
    
    async def _handle_member_remove(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Discord member leave event"""
        # Could implement cleanup logic here
        return {"status": "processed", "action": "member_remove"}
    
    async def _handle_message_sync(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message synchronization"""
        message_data = webhook_data.get("message", {})
        guild_id = webhook_data.get("guild_id")
        
        # Check if message should be synced based on channel and content
        if self._should_sync_message(message_data, guild_id):
            # Get target guilds for synchronization
            target_guilds = await self._get_sync_target_guilds(guild_id)
            
            if target_guilds:
                await self.sync_message(
                    source_guild_id=guild_id,
                    target_guild_ids=target_guilds,
                    message_content=message_data.get("content", ""),
                    author_name=message_data.get("author", {}).get("username", "Unknown"),
                    channel_type="announcement"
                )
        
        return {"status": "processed", "action": "message_sync"}
    
    def _should_sync_message(self, message_data: Dict[str, Any], guild_id: str) -> bool:
        """Determine if a message should be synchronized"""
        # Implement logic to determine if message should be synced
        # Could be based on channel, content, author permissions, etc.
        channel_id = message_data.get("channel_id")
        content = message_data.get("content", "")
        
        # Example: sync messages from announcement channels that start with [SYNC]
        return channel_id and content.startswith("[SYNC]")
    
    async def _get_sync_target_guilds(self, source_guild_id: str) -> List[str]:
        """Get target guilds for message synchronization"""
        # Get the organization for this guild
        source_guild = await self.get_guild(source_guild_id)
        if not source_guild or not source_guild.org_id:
            return []
        
        # Get all other guilds for the same organization
        target_guilds = []
        async for guild_doc in self.db.discord_guilds.find({
            "org_id": source_guild.org_id,
            "guild_id": {"$ne": source_guild_id},
            "sync_enabled": True
        }):
            target_guilds.append(guild_doc["guild_id"])
        
        return target_guilds
    
    async def _create_default_reminder_configs(self, guild_id: str):
        """Create default reminder configurations for a new guild"""
        default_configs = [
            {"reminder_type": ReminderType.EVENT_J3, "enabled": True},
            {"reminder_type": ReminderType.EVENT_J1, "enabled": True},
            {"reminder_type": ReminderType.EVENT_H1, "enabled": True},
            {"reminder_type": ReminderType.TOURNAMENT_START, "enabled": True},
        ]
        
        for config in default_configs:
            config["guild_id"] = guild_id
            config["id"] = str(uuid.uuid4())
            config["created_at"] = datetime.utcnow()
            config["updated_at"] = datetime.utcnow()
            
            await self.db.reminder_configs.insert_one(config)
    
    # Statistics and monitoring
    async def get_integration_stats(self) -> Dict[str, Any]:
        """Get Discord integration statistics"""
        stats = {}
        
        # Guild statistics
        stats["total_guilds"] = await self.db.discord_guilds.count_documents({})
        stats["active_guilds"] = await self.db.discord_guilds.count_documents({"status": "active"})
        
        # Job statistics
        stats["pending_jobs"] = await self.db.discord_jobs.count_documents({"status": "pending"})
        stats["failed_jobs"] = await self.db.discord_jobs.count_documents({"status": "failed"})
        
        # Webhook statistics
        stats["total_webhooks_sent"] = await self.db.webhook_logs.count_documents({"webhook_type": "outgoing"})
        stats["total_webhooks_received"] = await self.db.webhook_logs.count_documents({"webhook_type": "incoming"})
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        stats["recent_jobs"] = await self.db.discord_jobs.count_documents({"created_at": {"$gte": yesterday}})
        stats["recent_webhooks"] = await self.db.webhook_logs.count_documents({"created_at": {"$gte": yesterday}})
        
        return stats
    
    # New job processors for extended functionality
    async def _process_create_channels_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process create channels job"""
        payload = job.payload
        event_id = payload.get("event_id")
        guild_id = job.guild_id
        
        # Get event details
        event_doc = await self.db.events.find_one({"id": event_id})
        if not event_doc:
            raise ValueError("Event not found")
        
        # Create channels via bot API
        channel_data = {
            "guild_id": guild_id,
            "event_id": event_id,
            "event_name": event_doc["title"],
            "create_text": payload.get("create_text", True),
            "create_voice": payload.get("create_voice", True),
            "permissions": payload.get("permissions", {})
        }
        
        return await self.call_bot_api("channels/create", data=channel_data)
    
    async def _process_manage_roles_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process manage roles job"""
        payload = job.payload
        guild_id = job.guild_id
        
        role_data = {
            "guild_id": guild_id,
            "action": payload.get("action", "assign"),  # assign, remove, create
            "user_id": payload.get("user_id"),
            "role_id": payload.get("role_id"),
            "role_name": payload.get("role_name"),
            "role_permissions": payload.get("role_permissions", {})
        }
        
        return await self.call_bot_api("roles/manage", data=role_data)
    
    async def _process_sync_reactions_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process sync reactions job"""
        payload = job.payload
        guild_id = job.guild_id
        
        reaction_data = {
            "guild_id": guild_id,
            "message_id": payload.get("message_id"),
            "channel_id": payload.get("channel_id"),
            "reaction_data": payload.get("reaction_data", {}),
            "sync_type": payload.get("sync_type", "signup")
        }
        
        return await self.call_bot_api("reactions/sync", data=reaction_data)
    
    # Enhanced event management
    async def queue_discord_event_creation(self, event_id: str, guild_ids: List[str], 
                                           create_channels: bool = True, create_signup_message: bool = True):
        """Queue Discord scheduled event creation for multiple guilds"""
        for guild_id in guild_ids:
            # Check if guild has auto-event creation enabled
            guild = await self.get_guild(guild_id)
            if not guild or not guild.reminder_enabled:  # Using reminder_enabled as feature flag
                continue
            
            job_data = DiscordJobCreate(
                job_type=JobType.CREATE_DISCORD_EVENT,
                guild_id=guild_id,
                event_id=event_id,
                payload={
                    "event_id": event_id,
                    "create_channels": create_channels,
                    "create_signup_message": create_signup_message,
                    "signup_channel_id": guild.event_channel_id or guild.announcement_channel_id
                }
            )
            await self.queue_job(job_data)
    
    async def queue_discord_event_update(self, event_id: str, guild_ids: List[str]):
        """Queue Discord scheduled event updates for multiple guilds"""
        for guild_id in guild_ids:
            job_data = DiscordJobCreate(
                job_type=JobType.UPDATE_DISCORD_EVENT,
                guild_id=guild_id,
                event_id=event_id,
                payload={"event_id": event_id}
            )
            await self.queue_job(job_data)
    
    async def queue_discord_event_deletion(self, event_id: str, guild_ids: List[str]):
        """Queue Discord scheduled event deletion for multiple guilds"""
        for guild_id in guild_ids:
            job_data = DiscordJobCreate(
                job_type=JobType.DELETE_DISCORD_EVENT,
                guild_id=guild_id,
                event_id=event_id,
                payload={"event_id": event_id}
            )
            await self.queue_job(job_data)
    
    async def process_discord_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Discord interaction (buttons, select menus, etc.)"""
        from services.discord_events_service import DiscordEventsService
        events_service = DiscordEventsService()
        
        interaction_type = interaction_data.get("type")
        
        if interaction_type == 3:  # MESSAGE_COMPONENT
            custom_id = interaction_data.get("data", {}).get("custom_id", "")
            
            # Handle event signup interactions
            if any(prefix in custom_id for prefix in ["signup_", "withdraw_", "view_signups_", "select_role_"]):
                response = await events_service.handle_signup_interaction(interaction_data)
                return response.dict()
        
        return {
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "content": "❌ Interaction non prise en charge",
                "flags": 64  # EPHEMERAL
            }
        }