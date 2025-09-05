from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class WebhookType(str, Enum):
    INCOMING = "incoming"  # Received from Discord
    OUTGOING = "outgoing"  # Sent to Discord

class WebhookEvent(str, Enum):
    # Discord -> VerseLink
    GUILD_MEMBER_ADD = "guild_member_add"
    GUILD_MEMBER_REMOVE = "guild_member_remove"
    MESSAGE_CREATE = "message_create"
    MESSAGE_DELETE = "message_delete"
    CHANNEL_CREATE = "channel_create"
    ROLE_UPDATE = "role_update"
    
    # VerseLink -> Discord
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_CANCELLED = "event_cancelled"
    EVENT_REMINDER = "event_reminder"
    TOURNAMENT_CREATED = "tournament_created"
    TOURNAMENT_STARTED = "tournament_started"
    MATCH_RESULT = "match_result"
    ORG_ANNOUNCEMENT = "org_announcement"

class DiscordGuildStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    REMINDER = "reminder"
    ANNOUNCEMENT = "announcement"
    SYNC_MESSAGE = "sync_message"
    WEBHOOK_DELIVERY = "webhook_delivery"

# Discord Guild Management
class DiscordGuildBase(BaseModel):
    guild_id: str = Field(..., description="Discord Guild ID")
    guild_name: str = Field(..., min_length=1, max_length=100)
    owner_id: str = Field(..., description="Discord User ID of guild owner")
    webhook_url: Optional[str] = Field(None, description="Discord webhook URL for outgoing messages")
    announcement_channel_id: Optional[str] = Field(None, description="Channel for announcements")
    reminder_channel_id: Optional[str] = Field(None, description="Channel for reminders")
    sync_enabled: bool = Field(default=True, description="Enable message synchronization")
    reminder_enabled: bool = Field(default=True, description="Enable automatic reminders")

class DiscordGuildCreate(DiscordGuildBase):
    pass

class DiscordGuild(DiscordGuildBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    org_id: Optional[str] = Field(None, description="Associated organization ID")
    status: DiscordGuildStatus = Field(default=DiscordGuildStatus.ACTIVE)
    last_sync_at: Optional[datetime] = None
    webhook_verified: bool = Field(default=False)
    api_key: str = Field(default_factory=lambda: str(uuid.uuid4()), description="API key for bot authentication")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class DiscordGuildResponse(BaseModel):
    id: str
    guild_id: str
    guild_name: str
    owner_id: str
    org_id: Optional[str]
    org_name: Optional[str]
    status: str
    sync_enabled: bool
    reminder_enabled: bool
    webhook_verified: bool
    last_sync_at: Optional[datetime]
    created_at: datetime

# Webhook Management
class WebhookLogBase(BaseModel):
    webhook_type: WebhookType
    event_type: WebhookEvent
    guild_id: Optional[str] = Field(None, description="Discord Guild ID")
    payload: Dict[str, Any] = Field(default_factory=dict)
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None

class WebhookLog(WebhookLogBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    processed: bool = Field(default=False)
    retry_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class WebhookResponse(BaseModel):
    id: str
    webhook_type: str
    event_type: str
    guild_id: Optional[str]
    processed: bool
    response_code: Optional[int]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime

# Job Queue System
class DiscordJobBase(BaseModel):
    job_type: JobType
    guild_id: str = Field(..., description="Target Discord Guild ID")
    event_id: Optional[str] = Field(None, description="Related event/tournament ID")
    payload: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    
class DiscordJobCreate(DiscordJobBase):
    pass

class DiscordJob(DiscordJobBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = Field(default=JobStatus.PENDING)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class DiscordJobResponse(BaseModel):
    id: str
    job_type: str
    guild_id: str
    event_id: Optional[str]
    status: str
    retry_count: int
    max_retries: int
    scheduled_at: datetime
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

# Message Synchronization
class SyncedMessageBase(BaseModel):
    original_guild_id: str = Field(..., description="Source Discord Guild ID")
    original_channel_id: str = Field(..., description="Source channel ID")
    original_message_id: str = Field(..., description="Source message ID")
    content: str = Field(..., min_length=1, max_length=4000)
    author_id: str = Field(..., description="Discord User ID of author")
    author_name: str = Field(..., max_length=100)
    message_type: str = Field(default="announcement")

class SyncedMessage(SyncedMessageBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_deliveries: List[Dict[str, Any]] = Field(default_factory=list)  # List of guild_id and message_id pairs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class SyncedMessageResponse(BaseModel):
    id: str
    original_guild_id: str
    original_channel_id: str
    content: str
    author_name: str
    message_type: str
    target_deliveries: List[Dict[str, Any]]
    created_at: datetime

# Reminder Configuration
class ReminderType(str, Enum):
    EVENT_J3 = "event_j3"      # 3 days before event
    EVENT_J1 = "event_j1"      # 1 day before event
    EVENT_H1 = "event_h1"      # 1 hour before event
    TOURNAMENT_START = "tournament_start"
    TOURNAMENT_MATCH = "tournament_match"
    CHECK_IN_OPEN = "check_in_open"
    CUSTOM = "custom"

class ReminderConfigBase(BaseModel):
    guild_id: str = Field(..., description="Discord Guild ID")
    reminder_type: ReminderType
    enabled: bool = Field(default=True)
    channel_id: Optional[str] = Field(None, description="Target channel ID")
    custom_message: Optional[str] = Field(None, max_length=2000)
    offset_minutes: int = Field(default=0, description="Minutes before event for custom reminder")

class ReminderConfig(ReminderConfigBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class ReminderConfigResponse(BaseModel):
    id: str
    guild_id: str
    reminder_type: str
    enabled: bool
    channel_id: Optional[str]
    custom_message: Optional[str]
    offset_minutes: int
    created_at: datetime

# Bot API Authentication
class BotAuthToken(BaseModel):
    guild_id: str
    api_key: str
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

# Request/Response models for Discord Bot API
class EventAnnouncementRequest(BaseModel):
    event_id: str
    guild_ids: List[str] = Field(..., min_items=1)
    announcement_type: str = Field(..., pattern="^(created|updated|cancelled|reminder)$")
    custom_message: Optional[str] = Field(None, max_length=2000)

class TournamentAnnouncementRequest(BaseModel):
    tournament_id: str
    guild_ids: List[str] = Field(..., min_items=1)
    announcement_type: str = Field(..., regex="^(created|started|finished|match_result)$")
    custom_message: Optional[str] = Field(None, max_length=2000)

class MessageSyncRequest(BaseModel):
    source_guild_id: str
    target_guild_ids: List[str] = Field(..., min_items=1)
    message_content: str = Field(..., min_length=1, max_length=4000)
    author_name: str = Field(..., max_length=100)
    channel_type: str = Field(default="announcement")

class WebhookPayload(BaseModel):
    """Standard webhook payload structure"""
    event_type: WebhookEvent
    guild_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    signature: Optional[str] = None  # HMAC signature for verification

# Statistics and Analytics
class DiscordIntegrationStats(BaseModel):
    total_guilds: int = 0
    active_guilds: int = 0
    total_webhooks_sent: int = 0
    total_webhooks_received: int = 0
    pending_jobs: int = 0
    failed_jobs: int = 0
    total_synced_messages: int = 0
    last_24h_activity: Dict[str, int] = Field(default_factory=dict)