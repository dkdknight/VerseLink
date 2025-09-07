from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime

from database import get_database
from models.user import User
from models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrgMember, OrgMemberCreate, OrgMemberResponse, OrgMemberRole,
    Subscription, SubscriptionCreate, SubscriptionResponse
)
from middleware.auth import get_current_active_user

router = APIRouter()

async def get_org_member_role(db, org_id: str, user_id: str) -> Optional[OrgMemberRole]:
    """Get user's role in organization"""
    member_doc = await db.org_members.find_one({"org_id": org_id, "user_id": user_id})
    return OrgMemberRole(member_doc["role"]) if member_doc else None

async def require_org_permission(org_id: str, user: User, min_role: OrgMemberRole = OrgMemberRole.ADMIN):
    """Check if user has required permission in organization"""
    db = get_database()
    
    # Site admins have all permissions
    if user.is_site_admin:
        return True
        
    # Check if user is owner
    org_doc = await db.organizations.find_one({"id": org_id})
    if org_doc and org_doc["owner_id"] == user.id:
        return True
    
    # Check member role
    user_role = await get_org_member_role(db, org_id, user.id)
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    
    role_hierarchy = {
        OrgMemberRole.MEMBER: 1,
        OrgMemberRole.STAFF: 2,
        OrgMemberRole.ADMIN: 3
    }
    
    if role_hierarchy[user_role] < role_hierarchy[min_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return True

@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new organization"""
    db = get_database()
    
    # Check if name/tag already exists
    existing_org = await db.organizations.find_one({
        "$or": [
            {"name": org_data.name},
            {"tag": org_data.tag.upper()}
        ]
    })
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization name or tag already exists"
        )
    
    # Create organization
    org = Organization(**org_data.dict(), owner_id=current_user.id)
    await db.organizations.insert_one(org.dict())
    
    # Add owner as admin member
    owner_member = OrgMember(
        org_id=org.id,
        user_id=current_user.id,
        role=OrgMemberRole.ADMIN
    )
    await db.org_members.insert_one(owner_member.dict())
    
    return OrganizationResponse(**org.dict())

@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    query: str = "",
    visibility: Optional[str] = None,
    limit: int = 20,
    skip: int = 0
):
    """List organizations with search and filters"""
    db = get_database()
    
    # Build filter
    search_filter = {"visibility": {"$ne": "private"}}  # Hide private orgs from public listing
    
    if query:
        search_filter["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"tag": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    
    if visibility and visibility in ["public", "unlisted"]:
        search_filter["visibility"] = visibility
    
    # Execute search
    cursor = db.organizations.find(search_filter).skip(skip).limit(limit).sort("created_at", -1)
    orgs = []
    
    async for org_doc in cursor:
        org = Organization(**org_doc)
        orgs.append(OrganizationResponse(**org.dict()))
    
    return orgs

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: str):
    """Get organization details"""
    db = get_database()
    
    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    org = Organization(**org_doc)
    
    # Check visibility
    if org.visibility == "private":
        # TODO: Check if user is member for private orgs
        pass
    
    return OrganizationResponse(**org.dict())

@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_update: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update organization (admin only)"""
    await require_org_permission(org_id, current_user, OrgMemberRole.ADMIN)
    
    db = get_database()
    
    # Prepare update data
    update_data = {}
    for field, value in org_update.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    if not update_data:
        org_doc = await db.organizations.find_one({"id": org_id})
        return OrganizationResponse(**org_doc)
    
    # Add updated timestamp
    update_data["updated_at"] = datetime.utcnow()
    
    # Update organization
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": update_data}
    )
    
    # Get updated org
    updated_org_doc = await db.organizations.find_one({"id": org_id})
    return OrganizationResponse(**updated_org_doc)

@router.get("/{org_id}/members", response_model=List[OrgMemberResponse])
async def get_organization_members(org_id: str):
    """Get organization members"""
    db = get_database()
    
    # Check if org exists
    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get members with user details
    pipeline = [
        {"$match": {"org_id": org_id}},
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
            "$project": {
                "user_id": 1,
                "role": 1,
                "joined_at": 1,
                "handle": "$user.handle",
                "discord_username": "$user.discord_username",
                "avatar_url": "$user.avatar_url"
            }
        }
    ]
    
    members = []
    async for member_doc in db.org_members.aggregate(pipeline):
        members.append(OrgMemberResponse(**member_doc))
    
    return members

@router.post("/{org_id}/members", response_model=dict)
async def join_organization(
    org_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Join organization as member"""
    db = get_database()
    
    # Check if org exists and is joinable
    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    org = Organization(**org_doc)
    if org.visibility == "private":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot join private organization without invitation"
        )
    
    # Check if already member
    existing_member = await db.org_members.find_one({
        "org_id": org_id,
        "user_id": current_user.id
    })
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this organization"
        )
    
    # Add as member
    member = OrgMember(
        org_id=org_id,
        user_id=current_user.id,
        role=OrgMemberRole.MEMBER
    )
    await db.org_members.insert_one(member.dict())
    
    # Update member count
    await db.organizations.update_one(
        {"id": org_id},
        {"$inc": {"member_count": 1}}
    )
    
    return {"message": "Successfully joined organization"}

@router.delete("/{org_id}/members/{user_id}")
async def remove_organization_member(
    org_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Remove member from organization (admin only, or self)"""
    db = get_database()
    
    # Check if removing self or require admin permission
    if user_id != current_user.id:
        await require_org_permission(org_id, current_user, OrgMemberRole.ADMIN)
    
    # Cannot remove owner
    org_doc = await db.organizations.find_one({"id": org_id})
    if org_doc and org_doc["owner_id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove organization owner"
        )
    
    # Remove member
    result = await db.org_members.delete_one({
        "org_id": org_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Update member count
    await db.organizations.update_one(
        {"id": org_id},
        {"$inc": {"member_count": -1}}
    )
    
    return {"message": "Member removed successfully"}

@router.post("/{org_id}/events", response_model=dict)
async def create_organization_event(
    org_id: str,
    event_data: dict,  # Will be converted to EventCreate in the route
    current_user: User = Depends(get_current_active_user)
):
    """Create event for organization"""
    from models.event import EventCreate, EventResponse
    from services.event_service import EventService
    from utils.permissions import EventPermissions
    
    # Check permissions
    can_create = await EventPermissions.can_create_event(current_user, org_id)
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create events for this organization"
        )
    
    # Validate organization exists
    db = get_database()
    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    try:
        # Create event data model
        event_create = EventCreate(**event_data)
        
        # Create event
        event_service = EventService()
        event = await event_service.create_event(event_create, org_id, current_user.id)
        
        return {
            "message": "Event created successfully",
            "event_id": event.id,
            "slug": event.slug
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event"
        )

@router.post("/{org_id}/tournaments", response_model=dict)
async def create_organization_tournament(
    org_id: str,
    tournament_data: dict,  # Will be converted to TournamentCreate in the route
    current_user: User = Depends(get_current_active_user)
):
    """Create tournament for organization"""
    from models.tournament import TournamentCreate
    from services.tournament_service import TournamentService
    from utils.permissions import EventPermissions
    
    # Check permissions (reuse event permissions for now)
    can_create = await EventPermissions.can_create_event(current_user, org_id)
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create tournaments for this organization"
        )
    
    # Validate organization exists
    db = get_database()
    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    try:
        # Create tournament data model
        tournament_create = TournamentCreate(**tournament_data)
        
        # Create tournament
        tournament_service = TournamentService()
        tournament = await tournament_service.create_tournament(tournament_create, org_id, current_user.id)
        
        return {
            "message": "Tournament created successfully",
            "tournament_id": tournament.id,
            "slug": tournament.slug
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tournament"
        )