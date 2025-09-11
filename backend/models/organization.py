from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class OrgVisibility(str, Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"

class OrgMembershipPolicy(str, Enum):
    OPEN = "open"
    REQUEST_ONLY = "request_only"

class OrgMemberRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"

class JoinRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    tag: str = Field(..., min_length=2, max_length=10)
    description: Optional[str] = Field(None, max_length=1000)
    website_url: Optional[str] = None
    visibility: OrgVisibility = Field(default=OrgVisibility.PUBLIC)
    membership_policy: OrgMembershipPolicy = Field(default=OrgMembershipPolicy.OPEN)
    
    # Media fields
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    
    # Social links
    discord_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    twitch_url: Optional[str] = None
    
    @validator('tag')
    def tag_uppercase_alphanumeric(cls, v):
        v = v.upper()
        if not v.isalnum():
            raise ValueError('Tag must contain only letters and numbers')
        return v
    
    @validator('website_url', 'discord_url', 'twitter_url', 'youtube_url', 'twitch_url')
    def validate_absolute_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @validator('logo_url', 'banner_url')
    def validate_media_urls(cls, v):
        if v and not (
            v.startswith('http://') or v.startswith('https://') or v.startswith('/')
        ):
            raise ValueError('URL must start with http://, https://, or /')
        return v

class OrganizationCreate(OrganizationBase):
    discord_guild_id: Optional[str] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    website_url: Optional[str] = None
    visibility: Optional[OrgVisibility] = None
    membership_policy: Optional[OrgMembershipPolicy] = None
    discord_guild_id: Optional[str] = None
    
    # Media fields
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    
    # Social links
    discord_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    twitch_url: Optional[str] = None

    @validator('website_url', 'discord_url', 'twitter_url', 'youtube_url', 'twitch_url')
    def validate_absolute_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @validator('logo_url', 'banner_url')
    def validate_media_urls(cls, v):
        if v and not (
            v.startswith('http://') or v.startswith('https://') or v.startswith('/')
        ):
            raise ValueError('URL must start with http://, https://, or /')
        return v

class Organization(OrganizationBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_guild_id: Optional[str] = None
    owner_id: str
    member_count: int = Field(default=1)
    event_count: int = Field(default=0)
    tournament_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class OrganizationResponse(BaseModel):
    id: str
    name: str
    tag: str
    description: Optional[str]
    website_url: Optional[str]
    visibility: str
    membership_policy: str
    member_count: int
    event_count: int
    tournament_count: int
    created_at: datetime
    
    # Media fields
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    
    # Social links
    discord_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    twitch_url: Optional[str] = None
    
    # Owner info for permission checks
    owner_id: Optional[str] = None

class OrgMemberBase(BaseModel):
    role: OrgMemberRole = Field(default=OrgMemberRole.MEMBER)

class OrgMemberCreate(OrgMemberBase):
    user_id: str

class OrgMember(OrgMemberBase):
    org_id: str
    user_id: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class OrgMemberResponse(BaseModel):
    user_id: str
    handle: str
    discord_username: str
    avatar_url: Optional[str]
    role: str
    joined_at: datetime

class SubscriptionBase(BaseModel):
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SubscriptionCreate(SubscriptionBase):
    publisher_org_id: str

class Subscription(SubscriptionBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subscriber_org_id: str
    publisher_org_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SubscriptionResponse(BaseModel):
    id: str
    publisher_org_id: str
    publisher_name: str
    publisher_tag: str
    filters: Dict[str, Any]
    created_at: datetime

# Join Request Models
class JoinRequestBase(BaseModel):
    message: Optional[str] = Field(None, max_length=500)

class JoinRequestCreate(JoinRequestBase):
    pass

class JoinRequest(JoinRequestBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str
    user_id: str
    status: JoinRequestStatus = Field(default=JoinRequestStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    
    class Config:
        use_enum_values = True

class JoinRequestResponse(BaseModel):
    id: str
    org_id: str
    user_id: str
    user_handle: str
    user_avatar_url: Optional[str]
    message: Optional[str]
    status: str
    created_at: datetime
    processed_at: Optional[datetime]
    processed_by: Optional[str]

class JoinRequestUpdate(BaseModel):
    status: JoinRequestStatus
    
# Transfer Ownership Models
class OwnershipTransferRequest(BaseModel):
    new_owner_id: str
    confirmation: bool = Field(..., description="Must be True to confirm transfer")

# Media Upload Models
class MediaUploadResponse(BaseModel):
    url: str
    filename: str
    size: int