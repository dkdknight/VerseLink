from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional

from database import get_database
from models.user import User, UserRole
from models.notification import (
    Report, ReportCreate, ReportResponse, ReportStatus,
    ModerationActionRequest, AuditLogResponse
)
from services.moderation_service import ModerationService
from middleware.auth import get_current_active_user, require_roles, require_site_admin

router = APIRouter()
moderation_service = ModerationService()

@router.post("/reports", response_model=dict)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create an abuse report"""
    # Users cannot report themselves
    if report_data.reported_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot report yourself"
        )
    
    # Check if reported user exists
    db = get_database()
    reported_user = await db.users.find_one({"id": report_data.reported_user_id})
    if not reported_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reported user not found"
        )
    
    try:
        report = await moderation_service.create_report(report_data, current_user.id)
        return {
            "message": "Report submitted successfully",
            "report_id": report.id
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_site_admin)
):
    """List reports for admin review"""
    db = get_database()
    
    # Parse status filter
    report_status = None
    if status:
        try:
            report_status = ReportStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status value"
            )
    
    reports = await moderation_service.get_reports(
        status=report_status,
        limit=limit,
        skip=skip
    )
    
    # Get user details for reports
    response = []
    for report in reports:
        # Get reported user info
        reported_user = await db.users.find_one({"id": report.reported_user_id})
        reporter_user = await db.users.find_one({"id": report.reporter_user_id})
        handled_by_user = None
        
        if report.handled_by:
            handled_by_user = await db.users.find_one({"id": report.handled_by})
        
        response.append(ReportResponse(
            **report.dict(),
            reported_user_handle=reported_user["handle"] if reported_user else "Unknown",
            reporter_user_handle=reporter_user["handle"] if reporter_user else "Unknown",
            handled_by_handle=handled_by_user["handle"] if handled_by_user else None
        ))
    
    return response

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(require_site_admin)
):
    """Get report details"""
    db = get_database()
    
    report_doc = await db.reports.find_one({"id": report_id})
    if not report_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    report = Report(**report_doc)
    
    # Get user details
    reported_user = await db.users.find_one({"id": report.reported_user_id})
    reporter_user = await db.users.find_one({"id": report.reporter_user_id})
    handled_by_user = None
    
    if report.handled_by:
        handled_by_user = await db.users.find_one({"id": report.handled_by})
    
    return ReportResponse(
        **report.dict(),
        reported_user_handle=reported_user["handle"] if reported_user else "Unknown",
        reporter_user_handle=reporter_user["handle"] if reporter_user else "Unknown",
        handled_by_handle=handled_by_user["handle"] if handled_by_user else None
    )

@router.post("/reports/{report_id}/action")
async def handle_report(
    report_id: str,
    action_request: ModerationActionRequest,
    current_user: User = Depends(require_site_admin)
):
    """Take moderation action on a report"""
    try:
        await moderation_service.handle_report(
            report_id=report_id,
            action=action_request.action,
            admin_id=current_user.id,
            reason=action_request.reason,
            duration_hours=action_request.duration_hours,
            reputation_change=action_request.reputation_change
        )
        
        return {"message": "Moderation action applied successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/users/{user_id}/history")
async def get_user_moderation_history(
    user_id: str,
    current_user: User = Depends(require_site_admin)
):
    """Get moderation history for a user"""
    history = await moderation_service.get_user_moderation_history(user_id)
    return history

@router.get("/stats")
async def get_moderation_stats(
    current_user: User = Depends(require_site_admin)
):
    """Get moderation statistics"""
    stats = await moderation_service.get_moderation_stats()
    return stats

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_site_admin)
):
    """Get audit logs"""
    db = get_database()
    
    cursor = db.audit_logs.find().sort("created_at", -1).skip(skip).limit(limit)
    logs = []
    
    async for log_doc in cursor:
        # Get user details
        actor_user = None
        target_user = None
        
        if log_doc.get("actor_user_id"):
            actor_doc = await db.users.find_one({"id": log_doc["actor_user_id"]})
            actor_user = actor_doc["handle"] if actor_doc else "Unknown"
        
        if log_doc.get("target_user_id"):
            target_doc = await db.users.find_one({"id": log_doc["target_user_id"]})
            target_user = target_doc["handle"] if target_doc else "Unknown"
        
        logs.append(AuditLogResponse(
            **log_doc,
            actor_user_handle=actor_user,
            target_user_handle=target_user
        ))
    
    return logs

@router.post("/maintenance/unban-expired")
async def unban_expired_users(
    current_user: User = Depends(require_site_admin)
):
    """Unban users with expired temporary bans"""
    count = await moderation_service.check_and_unban_users()
    return {"message": f"Unbanned {count} users with expired bans"}