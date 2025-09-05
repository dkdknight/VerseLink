from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from database import get_database
from models.user import User
from models.tournament import (
    Tournament, TournamentCreate, TournamentUpdate, TournamentResponse, TournamentDetailResponse,
    Team, TeamCreate, TeamResponse, ScoreReport, AttachmentResponse,
    TournamentFormat, TournamentState
)
from services.tournament_service import TournamentService
from services.bracket_service import BracketService
from services.file_upload_service import FileUploadService
from utils.permissions import EventPermissions  # Reuse event permissions for now
from middleware.auth import get_current_active_user

router = APIRouter()
tournament_service = TournamentService()
bracket_service = BracketService()
file_service = FileUploadService()

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
async def get_tournament(tournament_id: str):
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
    
    # Get matches
    matches = []
    async for match_doc in db.matches.find({"tournament_id": tournament_doc["id"]}).sort("round", 1).sort("bracket_position", 1):
        # Get team names
        team_a_name = None
        team_b_name = None
        winner_team_name = None
        
        if match_doc.get("team_a_id"):
            team_a = await db.teams.find_one({"id": match_doc["team_a_id"]})
            team_a_name = team_a["name"] if team_a else None
        
        if match_doc.get("team_b_id"):
            team_b = await db.teams.find_one({"id": match_doc["team_b_id"]})
            team_b_name = team_b["name"] if team_b else None
        
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
        matches.append(MatchResponse(
            **match_doc,
            team_a_name=team_a_name,
            team_b_name=team_b_name,
            winner_team_name=winner_team_name,
            attachments=attachments,
            can_report=False,  # Will be set based on user permissions
            can_verify=False   # Will be set based on user permissions
        ))
    
    # Generate bracket visualization
    tournament_obj = Tournament(**tournament_doc)
    bracket = await bracket_service.generate_bracket_visualization(tournament_obj)
    
    return TournamentDetailResponse(
        **tournament_doc,
        org_name=org.get("name"),
        org_tag=org.get("tag"),
        teams=teams,
        matches=matches,
        bracket=bracket,
        my_team=None,  # Will be set in frontend
        can_create_team=tournament_doc.get("state") == TournamentState.OPEN_REGISTRATION,
        can_edit=False,  # Will be set based on user permissions
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