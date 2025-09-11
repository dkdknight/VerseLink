from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from typing import List, Optional
from datetime import datetime
import aiofiles
import uuid as uuid_lib
from pathlib import Path

from database import get_database
from models.user import User
from models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrgMember, OrgMemberBase, OrgMemberResponse, OrgMemberRole,
    JoinRequest, JoinRequestCreate, JoinRequestResponse, JoinRequestUpdate, JoinRequestStatus,
    OwnershipTransferRequest, OrgMembershipPolicy
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
        OrgMemberRole.MODERATOR: 2,
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
    # Exclude fields with None values (e.g. discord_guild_id) to avoid
    # unique index conflicts on optional fields.
    await db.organizations.insert_one(org.dict(exclude_none=True))
    
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

@router.patch("/{org_id}/members/{user_id}/role", response_model=dict)
async def update_organization_member_role(
    org_id: str,
    user_id: str,
    role_update: OrgMemberBase,
    current_user: User = Depends(get_current_active_user)
):
    """Update a member's role in the organization (admin only)"""
    await require_org_permission(org_id, current_user, OrgMemberRole.ADMIN)

    db = get_database()

    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org_doc["owner_id"] == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify owner's role")

    result = await db.org_members.update_one(
        {"org_id": org_id, "user_id": user_id},
        {"$set": {"role": role_update.role}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    return {"message": "Member role updated successfully"}

@router.post("/{org_id}/events", response_model=dict)
async def create_organization_event(
    org_id: str,
    event_data: dict,  # Will be converted to EventCreate in the route
    current_user: User = Depends(get_current_active_user)
):
    """Create event for organization"""
    from models.event import EventCreate
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
    except Exception:
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tournament"
        )

# Media Upload Endpoints
@router.post("/{org_id}/media/logo", response_model=dict)
async def upload_organization_logo(
    org_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload organization logo (admin only)"""
    await require_org_permission(org_id, current_user, OrgMemberRole.ADMIN)
    
    # Validate file type and size
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Read file to check size
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 10MB"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/organizations/logos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{org_id}_{uuid_lib.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)
    
    # Update organization with logo URL
    db = get_database()
    logo_url = f"/uploads/organizations/logos/{unique_filename}"
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": {"logo_url": logo_url, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Logo uploaded successfully", "logo_url": logo_url}

@router.post("/{org_id}/media/banner", response_model=dict)
async def upload_organization_banner(
    org_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload organization banner (admin only)"""
    await require_org_permission(org_id, current_user, OrgMemberRole.ADMIN)
    
    # Validate file type and size
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Read file to check size
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 10MB"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/organizations/banners")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{org_id}_{uuid_lib.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)
    
    # Update organization with banner URL
    db = get_database()
    banner_url = f"/uploads/organizations/banners/{unique_filename}"
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": {"banner_url": banner_url, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Banner uploaded successfully", "banner_url": banner_url}

# Join Request Endpoints
@router.post("/{org_id}/join-requests", response_model=dict)
async def create_join_request(
    org_id: str,
    request_data: JoinRequestCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a join request for organizations with request-only policy"""
    db = get_database()
    
    # Check if org exists
    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    org = Organization(**org_doc)
    
    # Check if organization accepts join requests
    if org.membership_policy != OrgMembershipPolicy.REQUEST_ONLY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This organization accepts direct membership"
        )
    
    # Check if already a member
    existing_member = await db.org_members.find_one({
        "org_id": org_id,
        "user_id": current_user.id
    })
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this organization"
        )
    
    # Check if already has pending request
    existing_request = await db.join_requests.find_one({
        "org_id": org_id,
        "user_id": current_user.id,
        "status": JoinRequestStatus.PENDING
    })
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending join request"
        )
    
    # Create join request
    join_request = JoinRequest(
        org_id=org_id,
        user_id=current_user.id,
        **request_data.dict()
    )
    await db.join_requests.insert_one(join_request.dict())
    
    return {"message": "Join request submitted successfully"}

@router.get("/{org_id}/join-requests", response_model=List[JoinRequestResponse])
async def get_join_requests(
    org_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get join requests for organization (admin/moderator only)"""
    await require_org_permission(org_id, current_user, OrgMemberRole.MODERATOR)
    
    db = get_database()
    
    # Get join requests with user details
    pipeline = [
        {"$match": {"org_id": org_id, "status": JoinRequestStatus.PENDING}},
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
                "id": 1,
                "org_id": 1,
                "user_id": 1,
                "user_handle": "$user.handle",
                "user_avatar_url": "$user.avatar_url",
                "message": 1,
                "status": 1,
                "created_at": 1,
                "processed_at": 1,
                "processed_by": 1
            }
        },
        {"$sort": {"created_at": -1}}
    ]
    
    requests = []
    async for request_doc in db.join_requests.aggregate(pipeline):
        requests.append(JoinRequestResponse(**request_doc))
    
    return requests

@router.patch("/{org_id}/join-requests/{request_id}", response_model=dict)
async def process_join_request(
    org_id: str,
    request_id: str,
    request_update: JoinRequestUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Accept or reject a join request (admin/moderator only)"""
    await require_org_permission(org_id, current_user, OrgMemberRole.MODERATOR)
    
    db = get_database()
    
    # Get join request
    request_doc = await db.join_requests.find_one({
        "id": request_id,
        "org_id": org_id,
        "status": JoinRequestStatus.PENDING
    })
    if not request_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Join request not found"
        )
    
    # Update request status
    await db.join_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": request_update.status,
                "processed_at": datetime.utcnow(),
                "processed_by": current_user.id
            }
        }
    )
    
    # If accepted, add user as member
    if request_update.status == JoinRequestStatus.ACCEPTED:
        member = OrgMember(
            org_id=org_id,
            user_id=request_doc["user_id"],
            role=OrgMemberRole.MEMBER
        )
        await db.org_members.insert_one(member.dict())
        
        # Update member count
        await db.organizations.update_one(
            {"id": org_id},
            {"$inc": {"member_count": 1}}
        )
        
        message = "Join request accepted and user added as member"
    else:
        message = "Join request rejected"
    
    return {"message": message}

# Ownership Transfer Endpoint
@router.post("/{org_id}/transfer-ownership", response_model=dict)
async def transfer_ownership(
    org_id: str,
    transfer_request: OwnershipTransferRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Transfer organization ownership (owner only)"""
    db = get_database()
    
    # Check if user is owner
    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if org_doc["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can transfer ownership"
        )
    
    if not transfer_request.confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ownership transfer must be confirmed"
        )
    
    # Check if new owner is a member
    new_owner_member = await db.org_members.find_one({
        "org_id": org_id,
        "user_id": transfer_request.new_owner_id
    })
    if not new_owner_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New owner must be a member of the organization"
        )
    
    # Transfer ownership
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": {"owner_id": transfer_request.new_owner_id, "updated_at": datetime.utcnow()}}
    )
    
    # Update roles: new owner becomes admin, old owner becomes admin
    await db.org_members.update_one(
        {"org_id": org_id, "user_id": transfer_request.new_owner_id},
        {"$set": {"role": OrgMemberRole.ADMIN}}
    )
    await db.org_members.update_one(
        {"org_id": org_id, "user_id": current_user.id},
        {"$set": {"role": OrgMemberRole.ADMIN}}
    )
    
    return {"message": "Ownership transferred successfully"}

# Delete Organization Endpoint
@router.delete("/{org_id}", response_model=dict)
async def delete_organization(
    org_id: str,
    confirmation: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """Delete organization (owner only)"""
    db = get_database()
    
    # Check if user is owner
    org_doc = await db.organizations.find_one({"id": org_id})
    if not org_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if org_doc["owner_id"] != current_user.id and not current_user.is_site_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete the organization"
        )
    
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization deletion must be confirmed"
        )
    
    # Delete related data
    await db.org_members.delete_many({"org_id": org_id})
    await db.join_requests.delete_many({"org_id": org_id})
    await db.events.delete_many({"org_id": org_id})
    await db.tournaments.delete_many({"org_id": org_id})
    
    # Delete organization
    await db.organizations.delete_one({"id": org_id})
    
    return {"message": "Organization deleted successfully"}