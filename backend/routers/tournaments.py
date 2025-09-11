from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path

from database import get_database
from models.user import User
from models.tournament import (
    Tournament, TournamentCreate, TournamentUpdate, TournamentResponse, TournamentDetailResponse,
    Team, TeamCreate, TeamUpdate, TeamResponse, ScoreReport, MatchSchedule, MatchForfeit, AttachmentResponse,
    TournamentFormat, TournamentState, MatchState, TeamInvitationCreate, TeamInvitationResponse,
    InvitationStatus, MatchDisputeCreate, MatchDisputeResponse, DisputeStatus,
    PlayerSearchCreate, PlayerSearchResponse,
)
from services.tournament_service import TournamentService
from services.bracket_service import BracketService
from services.file_upload_service import FileUploadService
from services.team_invitation_service import TeamInvitationService
from services.match_dispute_service import MatchDisputeService
from services.player_search_service import PlayerSearchService
from utils.permissions import EventPermissions  # Reuse event permissions for now
from middleware.auth import get_current_active_user, get_current_user_optional
from routers.organizations import require_org_permission
from models.organization import OrgMemberRole

router = APIRouter()
tournament_service = TournamentService()
bracket_service = BracketService()
file_service = FileUploadService()
invitation_service = TeamInvitationService()
dispute_service = MatchDisputeService()
player_search_service = PlayerSearchService()

@router.get("/", response_model=List[TournamentResponse])
async def list_tournaments(
    query: str = Query("", description="Search query"),
    format: Optional[str] = Query(None, description="Tournament format filter"),
    state: Optional[str] = Query(None, description="Tournament state filter"),
    org_id: Optional[str] = Query(None, description="Organization filter"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """List tournaments with filters"""
    db = get_database()
    
    # Build query
    filters = {}
    
    if query:
        filters["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    
    if format and format in [f.value for f in TournamentFormat]:
        filters["format"] = format
    
    if state and state in [s.value for s in TournamentState]:
        filters["state"] = state
    
    if org_id:
        filters["org_id"] = org_id
    
    # Get tournaments with organization info
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
        {
            "$lookup": {
                "from": "teams",
                "let": {"tournament_id": "$id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$tournament_id", "$$tournament_id"]}}},
                    {"$match": {"id": {"$eq": "$winner_team_id"}}}
                ],
                "as": "winner_team"
            }
        },
        {"$skip": skip},
        {"$limit": limit},
        {"$sort": {"start_at_utc": 1}}
    ]
    
    tournaments = []
    async for tournament_doc in db.tournaments.aggregate(pipeline):
        # Extract org info
        org = tournament_doc.pop("org", {})
        winner_team = tournament_doc.pop("winner_team", [])
        
        tournament_response = TournamentResponse(
            **tournament_doc,
            org_name=org.get("name"),
            org_tag=org.get("tag"),
            winner_team_name=winner_team[0]["name"] if winner_team else None,
            is_registration_open=tournament_doc.get("state") == TournamentState.OPEN_REGISTRATION,
            can_register=tournament_doc.get("state") == TournamentState.OPEN_REGISTRATION and tournament_doc.get("team_count", 0) < tournament_doc.get("max_teams", 0)
        )
        tournaments.append(tournament_response)
    
    return tournaments

@router.get("/{tournament_id}", response_model=TournamentDetailResponse)
async def get_tournament(
    tournament_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get tournament details with bracket"""
    db = get_database()
    
    # Get tournament with org info
    pipeline = [
        {"$match": {"$or": [{"id": tournament_id}, {"slug": tournament_id}]}},
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
    
    tournament_doc = None
    async for doc in db.tournaments.aggregate(pipeline):
        tournament_doc = doc
        break
    
    if not tournament_doc:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Extract org info
    org = tournament_doc.pop("org", {})
    
    # Get teams with member info
    teams = []
    pipeline_teams = [
        {"$match": {"tournament_id": tournament_doc["id"]}},
        {
            "$lookup": {
                "from": "team_members",
                "localField": "id",
                "foreignField": "team_id",
                "as": "members"
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "captain_user_id",
                "foreignField": "id",
                "as": "captain"
            }
        },
        {"$unwind": "$captain"},
        {"$sort": {"seed": 1, "created_at": 1}}
    ]
    
    async for team_doc in db.teams.aggregate(pipeline_teams):
        captain = team_doc.pop("captain", {})
        members_data = team_doc.pop("members", [])
        
        # Get member details
        members = []
        for member in members_data:
            user_doc = await db.users.find_one({"id": member["user_id"]})
            if user_doc:
                members.append({
                    "user_id": user_doc["id"],
                    "handle": user_doc["handle"],
                    "avatar_url": user_doc.get("avatar_url"),
                    "is_captain": member["is_captain"],
                    "joined_at": member["joined_at"]
                })
        
        teams.append(TeamResponse(
            **team_doc,
            captain_handle=captain["handle"],
            members=members
        ))

    user_can_verify = False
    if current_user:
        user_can_verify = await EventPermissions.can_edit_event(
            current_user, tournament_doc["org_id"], tournament_doc["created_by"]
        )
    
    # Get matches
    matches = []
    async for match_doc in db.matches.find({"tournament_id": tournament_doc["id"]}).sort("round", 1).sort("bracket_position", 1):
        # Get team names and docs
        team_a_doc = None
        team_b_doc = None
        team_a_name = None
        team_b_name = None
        winner_team_name = None
        
        if match_doc.get("team_a_id"):
            team_a_doc = await db.teams.find_one({"id": match_doc["team_a_id"]})
            team_a_name = team_a_doc["name"] if team_a_doc else None
        
        if match_doc.get("team_b_id"):
            team_b_doc = await db.teams.find_one({"id": match_doc["team_b_id"]})
            team_b_name = team_b_doc["name"] if team_b_doc else None
        
        if match_doc.get("winner_team_id"):
            winner = await db.teams.find_one({"id": match_doc["winner_team_id"]})
            winner_team_name = winner["name"] if winner else None
        
        # Get attachments
        attachments = []
        async for attachment_doc in db.attachments.find({"match_id": match_doc["id"]}):
            user_doc = await db.users.find_one({"id": attachment_doc["user_id"]})
            attachments.append({
                "id": attachment_doc["id"],
                "filename": attachment_doc["filename"],
                "file_size": attachment_doc["file_size"],
                "mime_type": attachment_doc["mime_type"],
                "attachment_type": attachment_doc["attachment_type"],
                "description": attachment_doc.get("description"),
                "uploaded_by": user_doc["handle"] if user_doc else "Unknown",
                "uploaded_at": attachment_doc["uploaded_at"],
                "download_url": f"/api/v1/attachments/{attachment_doc['id']}/download"
            })
        
        from models.tournament import MatchResponse

        can_report = False
        can_verify = user_can_verify
        if current_user:
            if team_a_doc and team_a_doc.get("captain_user_id") == current_user.id:
                if match_doc.get("reported_by") != current_user.id and match_doc.get("state") in [MatchState.PENDING.value, MatchState.REPORTED.value]:
                    can_report = True
            if not can_report and team_b_doc and team_b_doc.get("captain_user_id") == current_user.id:
                if match_doc.get("reported_by") != current_user.id and match_doc.get("state") in [MatchState.PENDING.value, MatchState.REPORTED.value]:
                    can_report = True

        matches.append(MatchResponse(
            **match_doc,
            team_a_name=team_a_name,
            team_b_name=team_b_name,
            team_a_captain_id=team_a_doc.get("captain_user_id") if team_a_doc else None,
            team_b_captain_id=team_b_doc.get("captain_user_id") if team_b_doc else None,
            winner_team_name=winner_team_name,
            attachments=attachments,
            can_report=can_report,
            can_verify=can_verify,
        ))
    
    # Generate bracket visualization
    tournament_obj = Tournament(**tournament_doc)
    bracket = await bracket_service.generate_bracket_visualization(tournament_obj)

    can_edit = user_can_verify
    
    return TournamentDetailResponse(
        **tournament_doc,
        org_name=org.get("name"),
        org_tag=org.get("tag"),
        teams=teams,
        matches=matches,
        bracket=bracket,
        my_team=None,  # Will be set in frontend
        can_create_team=tournament_doc.get("state") == TournamentState.OPEN_REGISTRATION,
        can_edit=can_edit,
        is_registration_open=tournament_doc.get("state") == TournamentState.OPEN_REGISTRATION,
        can_register=tournament_doc.get("state") == TournamentState.OPEN_REGISTRATION and tournament_doc.get("team_count", 0) < tournament_doc.get("max_teams", 0)
    )

@router.post("/{tournament_id}/teams", response_model=TeamResponse)
async def create_team(
    tournament_id: str,
    team_data: TeamCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create team for tournament"""
    try:
        team = await tournament_service.create_team(tournament_id, team_data, current_user.id)
        
        # Get team with captain info
        captain_doc = await get_database().users.find_one({"id": current_user.id})
        
        return TeamResponse(
            **team.dict(),
            captain_handle=captain_doc["handle"],
            members=[{
                "user_id": current_user.id,
                "handle": captain_doc["handle"],
                "avatar_url": captain_doc.get("avatar_url"),
                "is_captain": True,
                "joined_at": datetime.utcnow()
            }]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{tournament_id}/teams/{team_id}/join")
async def join_team(
    tournament_id: str,
    team_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Join a team"""
    try:
        await tournament_service.join_team(team_id, current_user.id)
        return {"message": "Joined team successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{tournament_id}/teams/{team_id}/members")
async def add_team_member(
    tournament_id: str,
    team_id: str,
    user_id: str = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """Add member to team"""
    try:
        await tournament_service.add_team_member(team_id, user_id, current_user.id)
        return {"message": "Member added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{tournament_id}/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    tournament_id: str,
    team_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Remove member from team"""
    try:
        await tournament_service.remove_team_member(team_id, user_id, current_user.id)
        return {"message": "Member removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/matches/{match_id}/schedule")
async def schedule_match(
    match_id: str,
    schedule: MatchSchedule,
    current_user: User = Depends(get_current_active_user)
):
    """Schedule a match"""
    try:
        confirmed = await tournament_service.schedule_match(match_id, schedule.scheduled_at, current_user.id)
        if confirmed:
            return {"message": "Match scheduled successfully"}
        return {"message": "Schedule proposal recorded, awaiting opponent confirmation"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/matches/{match_id}/report")
async def report_match_score(
    match_id: str,
    score_report: ScoreReport,
    current_user: User = Depends(get_current_active_user)
):
    """Report match score"""
    try:
        await tournament_service.report_match_score(match_id, score_report, current_user.id)
        return {"message": "Score reported successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/matches/{match_id}/verify")
async def verify_match_result(
    match_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Verify match result (referee/admin only)"""
    try:
        await tournament_service.verify_match_result(match_id, current_user.id)
        return {"message": "Match result verified successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/matches/{match_id}/forfeit")
async def forfeit_match(
    match_id: str,
    forfeit: MatchForfeit,
    current_user: User = Depends(get_current_active_user),
):
    """Forfeit a match (organizer/admin only)"""
    try:
        await tournament_service.forfeit_match(match_id, forfeit.winner_team_id, current_user, forfeit.notes)
        return {"message": "Match forfeited successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/matches/{match_id}/attachments", response_model=AttachmentResponse)
async def upload_match_attachment(
    match_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """Upload attachment for match (screenshot, video, etc.)"""
    try:
        attachment = await file_service.save_file(match_id, current_user.id, file, description)
        
        return AttachmentResponse(
            id=attachment.id,
            filename=attachment.filename,
            file_size=attachment.file_size,
            mime_type=attachment.mime_type,
            attachment_type=attachment.attachment_type.value,
            description=attachment.description,
            uploaded_by=current_user.handle,
            uploaded_at=attachment.uploaded_at,
            download_url=file_service.get_file_url(attachment)
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/attachments/{attachment_id}/download")
async def download_attachment(attachment_id: str):
    """Download attachment file"""
    attachment = await file_service.get_attachment_for_download(attachment_id)
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.mime_type
    )

@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete attachment"""
    try:
        success = await file_service.delete_attachment(attachment_id, current_user.id)
        if success:
            return {"message": "Attachment deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Attachment not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Team Management Routes

@router.get("/{tournament_id}/teams/{team_id}")
async def get_team_details(
    tournament_id: str,
    team_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed team information"""
    db = get_database()
    
    # Get team with member info
    pipeline = [
        {"$match": {"id": team_id, "tournament_id": tournament_id}},
        {
            "$lookup": {
                "from": "team_members",
                "localField": "id",
                "foreignField": "team_id",
                "as": "members"
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "captain_user_id",
                "foreignField": "id",
                "as": "captain"
            }
        },
        {"$unwind": "$captain"}
    ]
    
    team_doc = None
    async for doc in db.teams.aggregate(pipeline):
        team_doc = doc
        break
    
    if not team_doc:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get member details
    member_details = []
    for member in team_doc["members"]:
        user_doc = await db.users.find_one({"id": member["user_id"]})
        if user_doc:
            member_details.append({
                "user_id": member["user_id"],
                "handle": user_doc["handle"],
                "avatar_url": user_doc.get("avatar_url"),
                "is_captain": member["is_captain"],
                "joined_at": member["joined_at"]
            })
    
    # Check permissions
    is_captain = team_doc["captain_user_id"] == current_user.id
    is_member = current_user.id in [m["user_id"] for m in team_doc["members"]]
    
    team_response = {
        "id": team_doc["id"],
        "name": team_doc["name"],
        "tournament_id": team_doc["tournament_id"],
        "captain_user_id": team_doc["captain_user_id"],
        "captain_handle": team_doc["captain"]["handle"],
        "member_count": team_doc["member_count"],
        "wins": team_doc["wins"],
        "losses": team_doc["losses"],
        "points": team_doc["points"],
        "eliminated": team_doc["eliminated"],
        "seed": team_doc.get("seed"),
        "members": member_details,
        "created_at": team_doc["created_at"],
        "can_manage": is_captain,
        "is_member": is_member
    }
    
    return team_response

@router.put("/{tournament_id}/teams/{team_id}")
async def update_team(
    tournament_id: str,
    team_id: str,
    team_update: TeamUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update team information (captain only)"""
    db = get_database()
    
    # Get team and verify captain
    team_doc = await db.teams.find_one({"id": team_id, "tournament_id": tournament_id})
    if not team_doc:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team_doc["captain_user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Only team captain can update team")
    
    # Check if tournament allows updates
    tournament_doc = await db.tournaments.find_one({"id": tournament_id})
    if not tournament_doc:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    if tournament_doc["state"] not in ["open_registration", "registration_closed"]:
        raise HTTPException(status_code=400, detail="Cannot update team after tournament has started")
    
    # Update team
    update_dict = {}
    for field, value in team_update.dict(exclude_unset=True).items():
        if value is not None:
            # Check if name is unique
            if field == "name":
                existing_team = await db.teams.find_one({
                    "tournament_id": tournament_id,
                    "name": value,
                    "id": {"$ne": team_id}
                })
                if existing_team:
                    raise HTTPException(status_code=400, detail="Team name already taken")
            
            update_dict[field] = value
    
    if update_dict:
        await db.teams.update_one(
            {"id": team_id},
            {"$set": update_dict}
        )
    
    return {"message": "Team updated successfully"}

@router.delete("/{tournament_id}/teams/{team_id}")
async def delete_team(
    tournament_id: str,
    team_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete team (captain only, before tournament starts)"""
    db = get_database()
    
    # Get team and verify captain
    team_doc = await db.teams.find_one({"id": team_id, "tournament_id": tournament_id})
    if not team_doc:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team_doc["captain_user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Only team captain can delete team")
    
    # Check tournament state
    tournament_doc = await db.tournaments.find_one({"id": tournament_id})
    if not tournament_doc:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    if tournament_doc["state"] not in ["open_registration"]:
        raise HTTPException(status_code=400, detail="Cannot delete team after registration closes")
    
    # Delete team members
    await db.team_members.delete_many({"team_id": team_id})
    
    # Delete team
    await db.teams.delete_one({"id": team_id})
    
    # Update tournament team count
    await db.tournaments.update_one(
        {"id": tournament_id},
        {"$inc": {"team_count": -1}}
    )
    
    return {"message": "Team deleted successfully"}

@router.post("/{tournament_id}/teams/{team_id}/leave")
async def leave_team(
    tournament_id: str,
    team_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Leave team (non-captain members only)"""
    try:
        await tournament_service.remove_team_member(team_id, current_user.id, current_user.id)
        return {"message": "Left team successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Tournament Administration Routes

@router.post("/{tournament_id}/start")
async def start_tournament(
    tournament_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Start tournament (organizer, org admin or staff)"""
    db = get_database()
    
    # Get tournament and verify permissions
    tournament_doc = await db.tournaments.find_one({"id": tournament_id})
    if not tournament_doc:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Check if user is tournament creator or has sufficient org permissions
    if tournament_doc["created_by"] != current_user.id:
        # Allow organization admins and staff members to manage the tournament
        await require_org_permission(tournament_doc["org_id"], current_user, OrgMemberRole.STAFF)
    
    # Check tournament state
    if tournament_doc["state"] != "registration_closed":
        raise HTTPException(status_code=400, detail="Tournament must be in registration closed state to start")
    
    try:
        await tournament_service.start_tournament(tournament_id, current_user.id)
        return {"message": "Tournament started successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{tournament_id}/close-registration")
async def close_tournament_registration(
    tournament_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Close tournament registration (organizer, org admin or staff)"""
    db = get_database()
    
    # Get tournament and verify permissions
    tournament_doc = await db.tournaments.find_one({"id": tournament_id})
    if not tournament_doc:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Check if user is tournament creator or has sufficient org permissions
    if tournament_doc["created_by"] != current_user.id:
        await require_org_permission(tournament_doc["org_id"], current_user, OrgMemberRole.STAFF)
    
    # Check tournament state
    if tournament_doc["state"] != "open_registration":
        raise HTTPException(status_code=400, detail="Tournament registration is not open")
    
    # Update tournament state
    await db.tournaments.update_one(
        {"id": tournament_id},
        {"$set": {"state": "registration_closed"}}
    )
    
    return {"message": "Tournament registration closed successfully"}

@router.post("/{tournament_id}/reopen-registration")
async def reopen_tournament_registration(
    tournament_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Reopen tournament registration (organizer, org admin or staff)"""
    db = get_database()
    
    # Get tournament and verify permissions
    tournament_doc = await db.tournaments.find_one({"id": tournament_id})
    if not tournament_doc:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Check if user is tournament creator or org admin
    if tournament_doc["created_by"] != current_user.id:
        await require_org_permission(tournament_doc["org_id"], current_user, OrgMemberRole.STAFF)
    
    # Check tournament state
    if tournament_doc["state"] not in ["registration_closed", "draft"]:
        raise HTTPException(status_code=400, detail="Cannot reopen registration for this tournament state")
    
    # Update tournament state
    await db.tournaments.update_one(
        {"id": tournament_id},
        {"$set": {"state": "open_registration"}}
    )
    
    return {"message": "Tournament registration reopened successfully"}

# Team Invitation Routes

@router.post("/{tournament_id}/teams/{team_id}/invitations", response_model=Dict[str, str])
async def create_team_invitation(
    tournament_id: str,
    team_id: str,
    invitation_data: TeamInvitationCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a team invitation (captain only)"""
    try:
        await invitation_service.create_invitation(team_id, invitation_data, current_user.id)
        return {"message": "Invitation sent successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tournament_id}/teams/{team_id}/invitations", response_model=List[TeamInvitationResponse])
async def get_team_invitations(
    tournament_id: str,
    team_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get team invitations (captain only)"""
    try:
        return await invitation_service.get_team_invitations(team_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/invitations/{invitation_id}/respond")
async def respond_to_invitation(
    invitation_id: str,
    accept: bool = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """Respond to a team invitation"""
    try:
        await invitation_service.respond_to_invitation(invitation_id, current_user.id, accept)
        action = "accepted" if accept else "declined"
        return {"message": f"Invitation {action} successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/invitations/{invitation_id}")
async def cancel_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a team invitation (captain only)"""
    try:
        await invitation_service.cancel_invitation(invitation_id, current_user.id)
        return {"message": "Invitation cancelled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/invitations/me", response_model=List[TeamInvitationResponse])
async def get_my_invitations(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's invitations"""
    try:
        invitation_status = None
        if status and status in [s.value for s in InvitationStatus]:
            invitation_status = InvitationStatus(status)
        
        return await invitation_service.get_user_invitations(current_user.id, invitation_status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Match Dispute Routes

@router.post("/matches/{match_id}/dispute", response_model=Dict[str, str])
async def create_match_dispute(
    match_id: str,
    dispute_data: MatchDisputeCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a match dispute (team captain only)"""
    try:
        await dispute_service.create_dispute(match_id, dispute_data, current_user.id)
        return {"message": "Dispute created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/matches/{match_id}/disputes", response_model=List[MatchDisputeResponse])
async def get_match_disputes(
    match_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get disputes for a specific match"""
    try:
        disputes = await dispute_service.list_disputes(limit=50)
        # Filter by match_id
        return [d for d in disputes if d.match_id == match_id]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/disputes", response_model=List[MatchDisputeResponse])
async def list_disputes(
    tournament_id: Optional[str] = Query(None, description="Filter by tournament"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user)
):
    """List disputes with optional filters"""
    try:
        dispute_status = None
        if status and status in [s.value for s in DisputeStatus]:
            dispute_status = DisputeStatus(status)
        
        return await dispute_service.list_disputes(tournament_id, dispute_status, limit, skip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/disputes/{dispute_id}", response_model=MatchDisputeResponse)
async def get_dispute(
    dispute_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get dispute details"""
    dispute = await dispute_service.get_dispute(dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute

@router.post("/disputes/{dispute_id}/review")
async def set_dispute_under_review(
    dispute_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Set dispute under review (admin only)"""
    try:
        await dispute_service.set_dispute_under_review(dispute_id, current_user.id)
        return {"message": "Dispute set under review"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    approve: bool = Form(...),
    admin_response: str = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """Resolve a dispute (admin only)"""
    try:
        await dispute_service.resolve_dispute(dispute_id, current_user.id, admin_response, approve)
        action = "approved" if approve else "rejected"
        return {"message": f"Dispute {action} successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Player Search Routes

@router.post("/{tournament_id}/player-search", response_model=Dict[str, str])
async def create_player_search(
    tournament_id: str,
    search_data: PlayerSearchCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create or update player search for tournament"""
    try:
        await player_search_service.create_player_search(tournament_id, search_data, current_user.id)
        return {"message": "Player search created/updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tournament_id}/player-search", response_model=List[PlayerSearchResponse])
async def get_tournament_player_searches(
    tournament_id: str,
    role: Optional[str] = Query(None, description="Filter by preferred role"),
    experience: Optional[str] = Query(None, description="Filter by experience level"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user)
):
    """Get player searches for a tournament with optional filters"""
    try:
        if role or experience:
            return await player_search_service.search_players(tournament_id, role, experience, limit, skip)
        else:
            return await player_search_service.get_tournament_player_searches(tournament_id, limit, skip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/player-search/me", response_model=List[PlayerSearchResponse])
async def get_my_player_searches(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's player searches"""
    try:
        return await player_search_service.get_user_player_searches(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/player-search/{search_id}", response_model=Dict[str, str])
async def update_player_search(
    search_id: str,
    search_data: PlayerSearchCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a player search (owner only)"""
    try:
        await player_search_service.update_player_search(search_id, search_data, current_user.id)
        return {"message": "Player search updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/player-search/{search_id}/deactivate", response_model=Dict[str, str])
async def deactivate_player_search(
    search_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate a player search (owner only)"""
    try:
        await player_search_service.deactivate_player_search(search_id, current_user.id)
        return {"message": "Player search deactivated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/player-search/{search_id}", response_model=Dict[str, str])
async def delete_player_search(
    search_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a player search (owner only)"""
    try:
        await player_search_service.delete_player_search(search_id, current_user.id)
        return {"message": "Player search deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))