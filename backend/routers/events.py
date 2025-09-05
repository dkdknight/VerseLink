from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime, timedelta
import tempfile
import os

from database import get_database
from models.user import User
from models.event import (
    Event, EventCreate, EventUpdate, EventResponse, EventDetailResponse,
    EventSignupCreate, EventSignupUpdate, EventSignupResponse,
    EventType, EventVisibility, EventState, SignupStatus
)
from models.organization import Organization
from services.event_service import EventService
from services.calendar_service import CalendarService
from utils.permissions import EventPermissions
from middleware.auth import get_current_active_user

# Helper function to get optional user
async def get_optional_user(token: str = None) -> Optional[User]:
    """Get user from token if provided, otherwise return None"""
    if not token:
        return None
    try:
        from fastapi.security import HTTPAuthorizationCredentials
        from middleware.auth import get_current_user
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return await get_current_user(creds)
    except:
        return None

router = APIRouter()
event_service = EventService()
calendar_service = CalendarService()

@router.get("/", response_model=List[EventResponse])
async def list_events(
    query: str = Query("", description="Search query"),
    type: Optional[str] = Query(None, description="Event type filter"),
    org_id: Optional[str] = Query(None, description="Organization filter"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """List published events with filters"""
    db = get_database()
    
    # Build query
    filters = {"state": EventState.PUBLISHED, "visibility": {"$ne": "private"}}
    
    if query:
        filters["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"location": {"$regex": query, "$options": "i"}}
        ]
    
    if type and type in [t.value for t in EventType]:
        filters["type"] = type
    
    if org_id:
        filters["org_id"] = org_id
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        filters["start_at_utc"] = date_filter
    
    # Get events with organization info
    pipeline = [
        {"$match": filters},
        {
            "$lookup": {
                "from": "organizations",
                "localField": "org_id",
                "foreignField": "id",
                "as": "org"
            }
        },
        {"$unwind": "$org"},
        {"$skip": skip},
        {"$limit": limit},
        {"$sort": {"start_at_utc": 1}}
    ]
    
    events = []
    async for event_doc in db.events.aggregate(pipeline):
        # Extract org info
        org = event_doc.pop("org", {})
        
        event_response = EventResponse(
            **event_doc,
            org_name=org.get("name"),
            org_tag=org.get("tag"),
            is_full=event_doc.get("confirmed_count", 0) >= event_doc.get("max_participants", float('inf')) if event_doc.get("max_participants") else False,
            checkin_available=_is_checkin_available(event_doc.get("start_at_utc"))
        )
        events.append(event_response)
    
    return events

@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(event_id: str):
    """Get event details"""
    db = get_database()
    
    # Get event with organization info
    pipeline = [
        {"$match": {"$or": [{"id": event_id}, {"slug": event_id}]}},
        {
            "$lookup": {
                "from": "organizations",
                "localField": "org_id",
                "foreignField": "id",
                "as": "org"
            }
        },
        {"$unwind": "$org"}
    ]
    
    event_doc = None
    async for doc in db.events.aggregate(pipeline):
        event_doc = doc
        break
    
    if not event_doc:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check visibility permissions (simplified for Phase 2)
    if event_doc["visibility"] == "private":
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Extract org info
    org = event_doc.pop("org", {})
    
    # Get roles
    roles = []
    async for role_doc in db.event_roles.find({"event_id": event_doc["id"]}):
        # Count current signups
        current_signups = await db.event_signups.count_documents({
            "event_id": event_doc["id"],
            "role_id": role_doc["id"],
            "status": {"$in": [SignupStatus.CONFIRMED, SignupStatus.CHECKED_IN]}
        })
        
        waitlist_count = await db.event_signups.count_documents({
            "event_id": event_doc["id"],
            "role_id": role_doc["id"],
            "status": SignupStatus.WAITLIST
        })
        
        roles.append({
            **role_doc,
            "current_signups": current_signups,
            "waitlist_count": waitlist_count,
            "is_full": current_signups >= role_doc["capacity"]
        })
    
    # Get fleet ships
    fleet_ships = []
    async for ship_doc in db.fleet_ships.find({"event_id": event_doc["id"]}):
        fleet_ships.append(ship_doc)
    
    # Get signups with user info
    signups = []
    pipeline_signups = [
        {
            "$match": {
                "event_id": event_doc["id"],
                "status": {"$ne": SignupStatus.WITHDRAWN}
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},
        {
            "$lookup": {
                "from": "event_roles",
                "localField": "role_id",
                "foreignField": "id",
                "as": "role"
            }
        },
        {"$sort": {"created_at": 1}}
    ]
    
    async for signup_doc in db.event_signups.aggregate(pipeline_signups):
        user = signup_doc["user"]
        role = signup_doc.get("role", [{}])[0] if signup_doc.get("role") else {}
        
        signups.append(EventSignupResponse(
            id=signup_doc["id"],
            user_id=signup_doc["user_id"],
            user_handle=user["handle"],
            user_discord_username=user["discord_username"],
            user_avatar_url=user.get("avatar_url"),
            role_id=signup_doc.get("role_id"),
            role_name=role.get("name"),
            status=signup_doc["status"],
            position_in_waitlist=signup_doc.get("position_in_waitlist"),
            notes=signup_doc.get("notes"),
            ship_model=signup_doc.get("ship_model"),
            created_at=signup_doc["created_at"],
            checked_in_at=signup_doc.get("checked_in_at")
        ))
    
    # Check user's signup
    my_signup = None
    can_signup = False
    can_edit = False
    can_checkin = False
    
    if current_user:
        my_signup_doc = await db.event_signups.find_one({
            "event_id": event_doc["id"],
            "user_id": current_user.id,
            "status": {"$ne": SignupStatus.WITHDRAWN}
        })
        
        if my_signup_doc:
            # Find matching signup in the list
            my_signup = next((s for s in signups if s.user_id == current_user.id), None)
            can_checkin = (my_signup_doc["status"] == SignupStatus.CONFIRMED and 
                          _is_checkin_available(event_doc["start_at_utc"]))
        else:
            can_signup = (event_doc["state"] == EventState.PUBLISHED and 
                         event_doc["start_at_utc"] > datetime.utcnow())
        
        # Check edit permissions
        can_edit = await EventPermissions.can_edit_event(
            current_user, event_doc["org_id"], event_doc["created_by"]
        )
    
    return EventDetailResponse(
        **event_doc,
        org_name=org.get("name"),
        org_tag=org.get("tag"),
        roles=roles,
        fleet_ships=fleet_ships,
        signups=signups,
        my_signup=my_signup,
        can_signup=can_signup,
        can_edit=can_edit,
        can_checkin=can_checkin,
        is_full=event_doc.get("confirmed_count", 0) >= event_doc.get("max_participants", float('inf')) if event_doc.get("max_participants") else False,
        checkin_available=_is_checkin_available(event_doc.get("start_at_utc"))
    )

@router.post("/{event_id}/signups", response_model=EventSignupResponse)
async def signup_for_event(
    event_id: str,
    signup_data: EventSignupCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Sign up for event"""
    try:
        await event_service.signup_for_event(event_id, current_user.id, signup_data)
        
        # Return updated signup info
        db = get_database()
        pipeline = [
            {
                "$match": {
                    "event_id": event_id,
                    "user_id": current_user.id,
                    "status": {"$ne": SignupStatus.WITHDRAWN}
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "id",
                    "as": "user"
                }
            },
            {"$unwind": "$user"},
            {
                "$lookup": {
                    "from": "event_roles",
                    "localField": "role_id",
                    "foreignField": "id",
                    "as": "role"
                }
            }
        ]
        
        async for signup_doc in db.event_signups.aggregate(pipeline):
            user = signup_doc["user"]
            role = signup_doc.get("role", [{}])[0] if signup_doc.get("role") else {}
            
            return EventSignupResponse(
                id=signup_doc["id"],
                user_id=signup_doc["user_id"],
                user_handle=user["handle"],
                user_discord_username=user["discord_username"],
                user_avatar_url=user.get("avatar_url"),
                role_id=signup_doc.get("role_id"),
                role_name=role.get("name"),
                status=signup_doc["status"],
                position_in_waitlist=signup_doc.get("position_in_waitlist"),
                notes=signup_doc.get("notes"),
                ship_model=signup_doc.get("ship_model"),
                created_at=signup_doc["created_at"],
                checked_in_at=signup_doc.get("checked_in_at")
            )
        
        raise HTTPException(status_code=500, detail="Failed to retrieve signup")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}/signups/me")
async def withdraw_from_event(
    event_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Withdraw from event"""
    success = await event_service.withdraw_from_event(event_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Signup not found")
    
    return {"message": "Successfully withdrawn from event"}

@router.post("/{event_id}/checkin")
async def checkin_for_event(
    event_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Check in for event"""
    try:
        success = await event_service.checkin_for_event(event_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Confirmed signup not found")
        
        return {"message": "Successfully checked in"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{event_id}/ics")
async def download_event_ics(event_id: str):
    """Download event as iCal file"""
    db = get_database()
    
    # Get event with org info
    pipeline = [
        {"$match": {"$or": [{"id": event_id}, {"slug": event_id}]}},
        {
            "$lookup": {
                "from": "organizations",
                "localField": "org_id",
                "foreignField": "id",
                "as": "org"
            }
        },
        {"$unwind": "$org"}
    ]
    
    event_doc = None
    async for doc in db.events.aggregate(pipeline):
        event_doc = doc
        break
    
    if not event_doc:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Only allow download of public events or if user has access
    if event_doc["visibility"] == "private":
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Create Event and Organization objects
    org = event_doc.pop("org", {})
    from models.organization import Organization
    
    event = Event(**event_doc)
    org_obj = Organization(**org) if org else None
    
    # Generate iCal
    ical_data = calendar_service.generate_event_ics(event, org_obj)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ics', delete=False) as f:
        f.write(ical_data)
        temp_path = f.name
    
    # Return file response
    filename = f"{event.slug}.ics"
    
    def cleanup():
        try:
            os.unlink(temp_path)
        except:
            pass
    
    return FileResponse(
        temp_path,
        media_type='text/calendar',
        filename=filename,
        background=cleanup
    )

def _is_checkin_available(start_at_utc: datetime) -> bool:
    """Check if check-in is available for event"""
    if not start_at_utc:
        return False
    
    now = datetime.utcnow()
    time_until_start = (start_at_utc - now).total_seconds() / 60
    
    # Check-in available 30 minutes before to 15 minutes after start
    return -15 <= time_until_start <= 30