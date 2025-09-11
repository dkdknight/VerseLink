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
    GUILD_SCHEDULED_EVENT_CREATE = "guild_scheduled_event_create"
    GUILD_SCHEDULED_EVENT_UPDATE = "guild_scheduled_event_update"
    GUILD_SCHEDULED_EVENT_DELETE = "guild_scheduled_event_delete"
    GUILD_SCHEDULED_EVENT_USER_ADD = "guild_scheduled_event_user_add"
    GUILD_SCHEDULED_EVENT_USER_REMOVE = "guild_scheduled_event_user_remove"
    MESSAGE_REACTION_ADD = "message_reaction_add"
    MESSAGE_REACTION_REMOVE = "message_reaction_remove"
    INTERACTION_CREATE = "interaction_create"
    
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
    CREATE_DISCORD_EVENT = "create_discord_event"
    UPDATE_DISCORD_EVENT = "update_discord_event"
    DELETE_DISCORD_EVENT = "delete_discord_event"
    CREATE_CHANNELS = "create_channels"
    MANAGE_ROLES = "manage_roles"
    SYNC_REACTIONS = "sync_reactions"

# Discord Event Status matching Discord API
class DiscordEventStatus(str, Enum):
    SCHEDULED = "1"  # Discord uses integer strings
    ACTIVE = "2"
    COMPLETED = "3"
    CANCELLED = "4"

class DiscordEventEntityType(str, Enum):
    STAGE_INSTANCE = "1"
    VOICE = "2"
    EXTERNAL = "3"

# Discord Guild Management
class DiscordGuildBase(BaseModel):
    guild_id: str = Field(..., description="Discord Guild ID")
    guild_name: str = Field(..., min_length=1, max_length=100)
    owner_id: str = Field(..., description="Discord User ID of guild owner")
    webhook_url: Optional[str] = Field(None, description="Discord webhook URL for outgoing messages")
    announcement_channel_id: Optional[str] = Field(None, description="Channel for announcements")
    reminder_channel_id: Optional[str] = Field(None, description="Channel for reminders")
    event_channel_id: Optional[str] = Field(None, description="Channel for event management")
    sync_enabled: bool = Field(default=True, description="Enable message synchronization")
    reminder_enabled: bool = Field(default=True, description="Enable automatic reminders")
    auto_create_channels: bool = Field(default=True, description="Auto-create channels for events")
    auto_manage_roles: bool = Field(default=True, description="Auto-manage roles for events")

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
    auto_create_channels: bool
    auto_manage_roles: bool
    webhook_verified: bool
    last_sync_at: Optional[datetime]
    created_at: datetime

# Discord Scheduled Event Management
class DiscordEventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    scheduled_start_time: datetime
    scheduled_end_time: Optional[datetime] = None
    entity_type: DiscordEventEntityType = Field(default=DiscordEventEntityType.EXTERNAL)
    entity_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    channel_id: Optional[str] = Field(None, description="Voice/Stage channel ID")
    privacy_level: int = Field(default=2, description="Guild only")

class DiscordEventCreate(DiscordEventBase):
    guild_id: str
    verselink_event_id: str

class DiscordEvent(DiscordEventBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_event_id: str = Field(..., description="Discord scheduled event ID")
    guild_id: str = Field(..., description="Discord Guild ID")
    verselink_event_id: str = Field(..., description="Associated VerseLink event ID")
    status: DiscordEventStatus = Field(default=DiscordEventStatus.SCHEDULED)
    creator_id: Optional[str] = None
    user_count: int = Field(default=0, description="Number of interested users")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class DiscordEventResponse(BaseModel):
    id: str
    discord_event_id: str
    guild_id: str
    verselink_event_id: str
    name: str
    description: Optional[str]
    status: str
    scheduled_start_time: datetime
    scheduled_end_time: Optional[datetime]
    user_count: int
    created_at: datetime

# Interactive Message Management
class InteractionType(str, Enum):
    PING = "1"
    APPLICATION_COMMAND = "2"
    MESSAGE_COMPONENT = "3"
    APPLICATION_COMMAND_AUTOCOMPLETE = "4"
    MODAL_SUBMIT = "5"

class ComponentType(str, Enum):
    ACTION_ROW = "1"
    BUTTON = "2"
    SELECT_MENU = "3"
    TEXT_INPUT = "4"

class ButtonStyle(str, Enum):
    PRIMARY = "1"    # Blue
    SECONDARY = "2"  # Grey
    SUCCESS = "3"    # Green
    DANGER = "4"     # Red
    LINK = "5"       # Grey with link

class InteractiveMessageBase(BaseModel):
    guild_id: str
    channel_id: str
    message_content: str
    embed_data: Optional[Dict[str, Any]] = None
    components: List[Dict[str, Any]] = Field(default_factory=list)
    message_type: str = Field(default="event_signup")

class InteractiveMessage(InteractiveMessageBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_message_id: Optional[str] = None
    verselink_event_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True)

class InteractionResponse(BaseModel):
    type: int = Field(..., description="Interaction response type")
    data: Optional[Dict[str, Any]] = None

# Role Management
class DiscordRoleMapping(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    guild_id: str
    discord_role_id: str
    discord_role_name: str
    verselink_role_type: str = Field(..., description="event_participant, org_member, etc.")
    verselink_entity_id: Optional[str] = Field(None, description="Event ID, Org ID, etc.")
    auto_assign: bool = Field(default=False)
    auto_remove: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Channel Management  
class DiscordChannelMapping(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    guild_id: str
    discord_channel_id: str
    discord_channel_name: str
    channel_type: str = Field(..., description="text, voice, category")
    verselink_event_id: Optional[str] = None
    auto_created: bool = Field(default=False)
    auto_archive: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    announcement_type: str = Field(..., pattern="^(created|started|finished|match_result)$")
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
    discord_events_created: int = 0
    interactive_messages_sent: int = 0
    last_24h_activity: Dict[str, int] = Field(default_factory=dict)