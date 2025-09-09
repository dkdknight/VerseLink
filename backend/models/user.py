from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class UserRole(str, Enum):
    PLAYER = "player"
    ORGANIZER = "organizer"
    ORG_ADMIN = "org_admin"
    REFEREE = "referee"
    SITE_ADMIN = "site_admin"

class UserBase(BaseModel):
    handle: str = Field(..., min_length=3, max_length=32)
    email: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    timezone: str = Field(default="UTC")
    locale: str = Field(default="fr")
    dm_opt_in: bool = Field(default=False)
    
    @validator('handle')
    def handle_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Handle must contain only letters, numbers, hyphens and underscores')
        return v

class UserCreate(UserBase):
    discord_id: str
    discord_username: str
    avatar_url: Optional[str] = None

class UserUpdate(BaseModel):
    handle: Optional[str] = Field(None, min_length=3, max_length=32)
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = None
    locale: Optional[str] = None
    dm_opt_in: Optional[bool] = None
    
    @validator('handle')
    def handle_alphanumeric(cls, v):
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Handle must contain only letters, numbers, hyphens and underscores')
        return v

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_id: str
    discord_username: str
    avatar_url: Optional[str] = None
    roles: List[UserRole] = Field(default=[UserRole.PLAYER])
    reputation: int = Field(default=0)
    strikes: int = Field(default=0)
    is_site_admin: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    last_seen_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class UserResponse(BaseModel):
    id: str
    handle: str
    discord_username: str
    avatar_url: Optional[str]
    bio: Optional[str]
    timezone: str
    locale: str
    roles: List[str]
    reputation: int
    is_site_admin: bool
    is_verified: bool
    created_at: datetime
    
class UserProfile(UserResponse):
    email: Optional[str] = None
    dm_opt_in: bool
    strikes: int
    last_seen_at: Optional[datetime] = None