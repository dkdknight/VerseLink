from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from datetime import datetime, timezone
from enum import Enum
import uuid

class TournamentFormat(str, Enum):
    SINGLE_ELIMINATION = "se"  # Single Elimination
    DOUBLE_ELIMINATION = "de"  # Double Elimination
    ROUND_ROBIN = "rr"         # Round Robin
    SWISS = "swiss"            # Swiss System (future)

class TournamentState(str, Enum):
    DRAFT = "draft"
    OPEN_REGISTRATION = "open_registration"
    REGISTRATION_CLOSED = "registration_closed"
    ONGOING = "ongoing"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class MatchState(str, Enum):
    PENDING = "pending"
    LIVE = "live"
    REPORTED = "reported"
    VERIFIED = "verified"
    DISPUTED = "disputed"

class AttachmentType(str, Enum):
    SCREENSHOT = "screenshot"
    VIDEO = "video"
    LOG = "log"
    OTHER = "other"

class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"

class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"

class TournamentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    format: TournamentFormat
    start_at_utc: datetime
    max_teams: int = Field(..., ge=4, le=64)
    team_size: int = Field(..., ge=1, le=10)
    ruleset_id: Optional[str] = None
    prize_pool: Optional[str] = Field(None, max_length=200)
    banner_url: Optional[str] = None
    
    @validator('start_at_utc')
    def start_at_must_be_future(cls, v):
        if v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        if v <= datetime.utcnow():
            raise ValueError('Tournament start time must be in the future')
        return v

class TournamentCreate(TournamentBase):
    pass

class TournamentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    start_at_utc: Optional[datetime] = None
    max_teams: Optional[int] = Field(None, ge=4, le=64)
    team_size: Optional[int] = Field(None, ge=1, le=10)
    ruleset_id: Optional[str] = None
    prize_pool: Optional[str] = Field(None, max_length=200)
    banner_url: Optional[str] = None
    
    @validator('start_at_utc')
    def start_at_must_be_future(cls, v):
        if v:
            if v.tzinfo is not None:
                v = v.astimezone(timezone.utc).replace(tzinfo=None)
            if v <= datetime.utcnow():
                raise ValueError('Tournament start time must be in the future')
        return v

class Tournament(TournamentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    org_id: str
    created_by: str
    state: TournamentState = Field(default=TournamentState.OPEN_REGISTRATION)
    team_count: int = Field(default=0)
    rounds_total: int = Field(default=0)
    current_round: int = Field(default=0)
    winner_team_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class TournamentResponse(BaseModel):
    id: str
    slug: str
    name: str
    description: str
    format: str
    state: str
    start_at_utc: datetime
    max_teams: int
    team_size: int
    team_count: int
    rounds_total: int
    current_round: int
    org_id: str
    org_name: Optional[str] = None
    org_tag: Optional[str] = None
    prize_pool: Optional[str]
    banner_url: Optional[str]
    winner_team_id: Optional[str] = None
    winner_team_name: Optional[str] = None
    created_at: datetime
    created_by: str
    is_registration_open: bool = Field(default=False)
    can_register: bool = Field(default=False)

class TeamBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    
    @validator('name')
    def name_no_special_chars(cls, v):
        # Allow letters, numbers, spaces, hyphens, underscores
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Team name can only contain letters, numbers, spaces, hyphens and underscores')
        return v.strip()

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    
    @validator('name')
    def name_no_special_chars(cls, v):
        if v:
            import re
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
                raise ValueError('Team name can only contain letters, numbers, spaces, hyphens and underscores')
            return v.strip()
        return v

class Team(TeamBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tournament_id: str
    captain_user_id: str
    member_count: int = Field(default=1)
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    points: int = Field(default=0)
    eliminated: bool = Field(default=False)
    seed: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TeamMember(BaseModel):
    team_id: str
    user_id: str
    is_captain: bool = Field(default=False)
    joined_at: datetime = Field(default_factory=datetime.utcnow)

class TeamResponse(BaseModel):
    id: str
    name: str
    tournament_id: str
    captain_user_id: str
    captain_handle: str
    member_count: int
    wins: int
    losses: int
    points: int
    eliminated: bool
    seed: Optional[int]
    members: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

class MatchBase(BaseModel):
    round: int = Field(..., ge=1)
    bracket_position: int = Field(..., ge=0)
    scheduled_at: Optional[datetime] = None

class Match(MatchBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tournament_id: str
    team_a_id: Optional[str] = None  # Can be None for bye rounds
    team_b_id: Optional[str] = None
    winner_team_id: Optional[str] = None
    loser_team_id: Optional[str] = None
    score_a: Optional[int] = None
    score_b: Optional[int] = None
    state: MatchState = Field(default=MatchState.PENDING)
    reported_by: Optional[str] = None
    verified_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class MatchResponse(BaseModel):
    id: str
    tournament_id: str
    round: int
    bracket_position: int
    team_a_id: Optional[str]
    team_a_name: Optional[str]
    team_b_id: Optional[str]
    team_b_name: Optional[str]
    winner_team_id: Optional[str]
    winner_team_name: Optional[str]
    score_a: Optional[int]
    score_b: Optional[int]
    state: str
    scheduled_at: Optional[datetime]
    reported_by: Optional[str]
    verified_by: Optional[str]
    notes: Optional[str]
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    can_report: bool = Field(default=False)
    can_verify: bool = Field(default=False)
    created_at: datetime

class ScoreReport(BaseModel):
    score_a: int = Field(..., ge=0)
    score_b: int = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('score_a', 'score_b')
    def scores_must_be_different(cls, v, values):
        if 'score_a' in values and v == values['score_a']:
            raise ValueError('Scores cannot be tied - there must be a winner')
        return v

class MatchSchedule(BaseModel):
    scheduled_at: datetime


class MatchForfeit(BaseModel):
    winner_team_id: str
    notes: Optional[str] = Field(None, max_length=500)

class Attachment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    user_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    attachment_type: AttachmentType
    description: Optional[str] = Field(None, max_length=200)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class AttachmentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    mime_type: str
    attachment_type: str
    description: Optional[str]
    uploaded_by: str
    uploaded_at: datetime
    download_url: str

class TournamentDetailResponse(TournamentResponse):
    teams: List[TeamResponse] = Field(default_factory=list)
    matches: List[MatchResponse] = Field(default_factory=list)
    bracket: Dict[str, Any] = Field(default_factory=dict)
    my_team: Optional[TeamResponse] = None
    can_create_team: bool = Field(default=False)
    can_edit: bool = Field(default=False)

class BracketNode(BaseModel):
    match_id: str
    round: int
    position: int
    team_a: Optional[Dict[str, Any]] = None
    team_b: Optional[Dict[str, Any]] = None
    winner: Optional[Dict[str, Any]] = None
    score_a: Optional[int] = None
    score_b: Optional[int] = None
    state: str
    next_match_id: Optional[str] = None
    previous_matches: List[str] = Field(default_factory=list)

# Team Invitation System
class TeamInvitation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    team_id: str
    tournament_id: str
    invited_user_id: str
    invited_by: str  # Captain user ID
    status: InvitationStatus = Field(default=InvitationStatus.PENDING)
    message: Optional[str] = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    responded_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class TeamInvitationCreate(BaseModel):
    invited_user_handle: str = Field(..., min_length=2, max_length=50)
    message: Optional[str] = Field(None, max_length=500)

class TeamInvitationResponse(BaseModel):
    id: str
    team_id: str
    team_name: str
    tournament_id: str
    tournament_name: str
    invited_user_id: str
    invited_user_handle: str
    invited_by: str
    invited_by_handle: str
    status: str
    message: Optional[str]
    created_at: datetime
    expires_at: datetime
    responded_at: Optional[datetime]

# Match Dispute System
class MatchDispute(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    disputed_by: str  # User ID who filed the dispute
    dispute_reason: str = Field(..., min_length=10, max_length=1000)
    status: DisputeStatus = Field(default=DisputeStatus.OPEN)
    admin_response: Optional[str] = Field(None, max_length=1000)
    resolved_by: Optional[str] = None  # Admin user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class MatchDisputeCreate(BaseModel):
    dispute_reason: str = Field(..., min_length=10, max_length=1000)

class MatchDisputeResponse(BaseModel):
    id: str
    match_id: str
    match_details: Dict[str, Any]
    disputed_by: str
    disputed_by_handle: str
    dispute_reason: str
    status: str
    admin_response: Optional[str]
    resolved_by: Optional[str]
    resolved_by_handle: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

# Player Search and Recruitment
class PlayerSearch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tournament_id: str
    looking_for_team: bool = Field(default=True)
    preferred_role: Optional[str] = Field(None, max_length=100)
    experience_level: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PlayerSearchCreate(BaseModel):
    preferred_role: Optional[str] = Field(None, max_length=100)
    experience_level: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

class PlayerSearchResponse(BaseModel):
    id: str
    user_id: str
    user_handle: str
    user_avatar_url: Optional[str]
    tournament_id: str
    tournament_name: str
    looking_for_team: bool
    preferred_role: Optional[str]
    experience_level: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime