from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class NotificationType(str, Enum):
    # Event notifications
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_CANCELLED = "event_cancelled"
    EVENT_REMINDER = "event_reminder"
    EVENT_SIGNUP_CONFIRMED = "event_signup_confirmed"
    EVENT_CHECKIN_AVAILABLE = "event_checkin_available"
    
    # Tournament notifications  
    TOURNAMENT_CREATED = "tournament_created"
    TOURNAMENT_STARTED = "tournament_started"
    TEAM_INVITED = "team_invited"
    MATCH_SCHEDULED = "match_scheduled"
    MATCH_RESULT = "match_result"
    MATCH_DISPUTED = "match_disputed"
    TOURNAMENT_WON = "tournament_won"
    EVENT_CHAT_MESSAGE = "event_chat_message"
    MATCH_CHAT_MESSAGE = "match_chat_message"
    
    # Organization notifications
    ORG_MEMBER_JOINED = "org_member_joined"
    ORG_ROLE_CHANGED = "org_role_changed"
    ORG_EVENT_PUBLISHED = "org_event_published"
    
    # Moderation notifications
    WARNING_RECEIVED = "warning_received"
    STRIKE_RECEIVED = "strike_received"
    REPUTATION_CHANGED = "reputation_changed"
    ACCOUNT_SUSPENDED = "account_suspended"
    
    # System notifications
    WELCOME = "welcome"
    SYSTEM_UPDATE = "system_update"
    MAINTENANCE = "maintenance"

class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationBase(BaseModel):
    type: NotificationType
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    data: Dict[str, Any] = Field(default_factory=dict)  # Additional context data
    action_url: Optional[str] = None  # URL to redirect when clicked

class NotificationCreate(NotificationBase):
    user_id: str

class Notification(NotificationBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    priority: str
    data: Dict[str, Any]
    action_url: Optional[str]
    read_at: Optional[datetime]
    created_at: datetime
    is_read: bool = Field(default=False)
    time_ago: str = ""  # Will be calculated

class NotificationPreferenceType(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    DISCORD_DM = "discord_dm"  # For future Discord integration

class NotificationPreferenceBase(BaseModel):
    notification_type: NotificationType
    in_app_enabled: bool = Field(default=True)
    email_enabled: bool = Field(default=False)
    discord_dm_enabled: bool = Field(default=False)

class NotificationPreference(NotificationPreferenceBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class NotificationPreferenceUpdate(BaseModel):
    preferences: Dict[str, Dict[str, bool]]  # {notification_type: {in_app: bool, email: bool, discord_dm: bool}}

class NotificationStats(BaseModel):
    total_count: int
    unread_count: int
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)

class ReportType(str, Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    CHEATING = "cheating"
    NO_SHOW = "no_show"
    GRIEFING = "griefing"
    OTHER = "other"

class ReportStatus(str, Enum):
    PENDING = "pending"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class ReportBase(BaseModel):
    reported_user_id: str
    type: ReportType
    reason: str = Field(..., min_length=10, max_length=1000)
    context_url: Optional[str] = None  # URL where incident occurred
    additional_info: Dict[str, Any] = Field(default_factory=dict)

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reporter_user_id: str
    status: ReportStatus = Field(default=ReportStatus.PENDING)
    admin_notes: Optional[str] = None
    action_taken: Optional[str] = None
    handled_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class ReportResponse(BaseModel):
    id: str
    reported_user_id: str
    reported_user_handle: str
    reporter_user_id: str
    reporter_user_handle: str
    type: str
    reason: str
    status: str
    context_url: Optional[str]
    admin_notes: Optional[str]
    action_taken: Optional[str]
    handled_by: Optional[str]
    handled_by_handle: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

class ModerationAction(str, Enum):
    WARNING = "warning"
    STRIKE = "strike"
    TEMPORARY_BAN = "temporary_ban"
    PERMANENT_BAN = "permanent_ban"
    REPUTATION_PENALTY = "reputation_penalty"
    DISMISS = "dismiss"

class ModerationActionRequest(BaseModel):
    action: ModerationAction
    reason: str = Field(..., min_length=5, max_length=500)
    duration_hours: Optional[int] = None  # For temporary bans
    reputation_change: Optional[int] = None  # For reputation penalties

class AuditLogAction(str, Enum):
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    REPORT_CREATED = "report_created"
    REPORT_RESOLVED = "report_resolved"
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_DELETED = "event_deleted"
    TOURNAMENT_CREATED = "tournament_created"
    ORGANIZATION_CREATED = "organization_created"
    MODERATION_ACTION = "moderation_action"

class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: AuditLogAction
    actor_user_id: Optional[str] = None  # Who performed the action
    target_user_id: Optional[str] = None  # Who was affected (if applicable)
    target_type: Optional[str] = None  # Type of object affected (event, tournament, etc.)
    target_id: Optional[str] = None  # ID of object affected
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class AuditLogResponse(BaseModel):
    id: str
    action: str
    actor_user_id: Optional[str]
    actor_user_handle: Optional[str]
    target_user_id: Optional[str]
    target_user_handle: Optional[str]
    target_type: Optional[str]
    target_id: Optional[str]
    details: Dict[str, Any]
    created_at: datetime