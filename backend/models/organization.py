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
    
    @validator('tag')
    def tag_uppercase_alphanumeric(cls, v):
        v = v.upper()
        if not v.isalnum():
            raise ValueError('Tag must contain only letters and numbers')
        return v

class OrganizationCreate(OrganizationBase):
    discord_guild_id: Optional[str] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    website_url: Optional[str] = None
    visibility: Optional[OrgVisibility] = None
    discord_guild_id: Optional[str] = None

class Organization(OrganizationBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_guild_id: Optional[str] = None
    logo_path: Optional[str] = None
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
    logo_path: Optional[str]
    visibility: str
    member_count: int
    event_count: int
    tournament_count: int
    created_at: datetime

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