from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class EventType(str, Enum):
    RAID = "raid"
    COURSE = "course"
    PVP = "pvp"
    FPS = "fps"
    SALVAGING = "salvaging"
    LOGISTIQUE = "logistique"
    EXPLORATION = "exploration"
    MINING = "mining"
    TRADING = "trading"
    ROLEPLAY = "roleplay"
    AUTRE = "autre"

class EventVisibility(str, Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"

class EventState(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class SignupStatus(str, Enum):
    WAITLIST = "waitlist"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    WITHDRAWN = "withdrawn"
    KICKED = "kicked"
    BANNED = "banned"
    NO_SHOW = "no_show"

class RulesetBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    body: str = Field(..., max_length=5000)
    visibility: EventVisibility = Field(default=EventVisibility.PUBLIC)

class Ruleset(RulesetBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RulesetResponse(BaseModel):
    id: str
    name: str
    body: str
    visibility: str
    created_at: datetime

class EventRoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    capacity: int = Field(..., ge=1, le=100)
    description: Optional[str] = Field(None, max_length=200)

class EventRoleCreate(EventRoleBase):
    pass

class EventRole(EventRoleBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    current_signups: int = Field(default=0)
    waitlist_count: int = Field(default=0)

class EventRoleResponse(EventRoleBase):
    id: str
    current_signups: int
    waitlist_count: int
    is_full: bool = Field(default=False)

class FleetShipBase(BaseModel):
    ship_model: str = Field(..., min_length=2, max_length=100)
    required_crew: int = Field(..., ge=1, le=50)
    notes: Optional[str] = Field(None, max_length=300)

class FleetShipCreate(FleetShipBase):
    pass

class FleetShip(FleetShipBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str

class FleetShipResponse(FleetShipBase):
    id: str

class EventBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    type: EventType
    start_at_utc: datetime
    duration_minutes: int = Field(..., ge=15, le=1440)  # 15 min to 24h
    location: Optional[str] = Field(None, max_length=100)
    visibility: EventVisibility = Field(default=EventVisibility.PUBLIC)
    max_participants: Optional[int] = Field(None, ge=1, le=500)
    ruleset_id: Optional[str] = None
    banner_url: Optional[str] = None
    allowed_org_ids: List[str] = Field(default_factory=list)
    
    @validator('start_at_utc')
    def start_at_must_be_future(cls, v):
        if v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        if v <= datetime.utcnow():
            raise ValueError('Event start time must be in the future')
        return v

class EventCreate(EventBase):
    roles: List[EventRoleCreate] = Field(default_factory=list)
    fleet_ships: List[FleetShipCreate] = Field(default_factory=list)

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    type: Optional[EventType] = None
    start_at_utc: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=1440)
    location: Optional[str] = Field(None, max_length=100)
    visibility: Optional[EventVisibility] = None
    max_participants: Optional[int] = Field(None, ge=1, le=500)
    ruleset_id: Optional[str] = None
    banner_url: Optional[str] = None
    allowed_org_ids: Optional[List[str]] = None
    
    @validator('start_at_utc')
    def start_at_must_be_future(cls, v):
        if v:
            if v.tzinfo is not None:
                v = v.astimezone(timezone.utc).replace(tzinfo=None)
            if v <= datetime.utcnow():
                raise ValueError('Event start time must be in the future')
        return v

class Event(EventBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    org_id: str
    created_by: str
    state: EventState = Field(default=EventState.PUBLISHED)
    signup_count: int = Field(default=0)
    confirmed_count: int = Field(default=0)
    checkin_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class EventResponse(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    type: str
    start_at_utc: datetime
    duration_minutes: int
    location: Optional[str]
    visibility: str
    state: str
    org_id: str
    org_name: Optional[str] = None
    org_tag: Optional[str] = None
    max_participants: Optional[int]
    signup_count: int
    confirmed_count: int
    checkin_count: int
    banner_url: Optional[str]
    created_at: datetime
    created_by: str
    allowed_org_ids: List[str] = Field(default_factory=list)
    roles: List[EventRoleResponse] = Field(default_factory=list)
    fleet_ships: List[FleetShipResponse] = Field(default_factory=list)
    is_full: bool = Field(default=False)
    checkin_available: bool = Field(default=False)

class EventSignupBase(BaseModel):
    role_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    ship_model: Optional[str] = Field(None, max_length=100)

class EventSignupCreate(EventSignupBase):
    pass

class EventSignupUpdate(BaseModel):
    role_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    ship_model: Optional[str] = Field(None, max_length=100)

class EventSignup(EventSignupBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    user_id: str
    status: SignupStatus = Field(default=SignupStatus.WAITLIST)
    position_in_waitlist: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    checked_in_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class EventSignupResponse(BaseModel):
    id: str
    user_id: str
    user_handle: str
    user_discord_username: str
    user_avatar_url: Optional[str]
    role_id: Optional[str]
    role_name: Optional[str]
    status: str
    position_in_waitlist: Optional[int]
    notes: Optional[str]
    ship_model: Optional[str]
    created_at: datetime
    checked_in_at: Optional[datetime]

class EventDetailResponse(EventResponse):
    signups: List[EventSignupResponse] = Field(default_factory=list)
    my_signup: Optional[EventSignupResponse] = None
    can_signup: bool = Field(default=False)
    can_edit: bool = Field(default=False)
    can_checkin: bool = Field(default=False)