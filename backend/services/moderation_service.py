from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from database import get_database
from models.notification import (
    Report, ReportCreate, ReportStatus, ModerationAction, 
    AuditLog, AuditLogAction
)
from models.user import User
from services.notification_service import NotificationService

class ModerationService:
    def __init__(self):
        self.db = get_database()
        self.notification_service = NotificationService()
    
    async def create_report(self, report_data: ReportCreate, reporter_id: str) -> Report:
        """Create a new abuse report"""
        # Check if user already reported this user recently (prevent spam)
        recent_report = await self.db.reports.find_one({
            "reporter_user_id": reporter_id,
            "reported_user_id": report_data.reported_user_id,
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
        })
        
        if recent_report:
            raise ValueError("You can only report a user once per 24 hours")
        
        # Create report
        report = Report(
            **report_data.dict(),
            reporter_user_id=reporter_id
        )
        
        await self.db.reports.insert_one(report.dict())
        
        # Log the action
        await self._create_audit_log(
            action=AuditLogAction.REPORT_CREATED,
            actor_user_id=reporter_id,
            target_user_id=report.reported_user_id,
            details={
                "report_id": report.id,
                "type": report.type,
                "reason": report.reason[:100]  # Truncate for log
            }
        )
        
        return report
    
    async def get_reports(
        self,
        status: Optional[ReportStatus] = None,
        limit: int = 20,
        skip: int = 0
    ) -> List[Report]:
        """Get reports for admin review"""
        query = {}
        if status:
            query["status"] = status
        
        cursor = self.db.reports.find(query).sort("created_at", -1).skip(skip).limit(limit)
        reports = []
        
        async for report_doc in cursor:
            reports.append(Report(**report_doc))
        
        return reports
    
    async def get_user_reports(self, user_id: str, limit: int = 10) -> List[Report]:
        """Get reports against a specific user"""
        cursor = self.db.reports.find({"reported_user_id": user_id}).sort("created_at", -1).limit(limit)
        reports = []
        
        async for report_doc in cursor:
            reports.append(Report(**report_doc))
        
        return reports
    
    async def handle_report(
        self,
        report_id: str,
        action: ModerationAction,
        admin_id: str,
        reason: str,
        duration_hours: Optional[int] = None,
        reputation_change: Optional[int] = None
    ) -> bool:
        """Handle a report with moderation action"""
        # Get report
        report_doc = await self.db.reports.find_one({"id": report_id})
        if not report_doc:
            raise ValueError("Report not found")
        
        report = Report(**report_doc)
        
        if report.status != ReportStatus.PENDING:
            raise ValueError("Report is already handled")
        
        # Get reported user
        user_doc = await self.db.users.find_one({"id": report.reported_user_id})
        if not user_doc:
            raise ValueError("Reported user not found")
        
        user = User(**user_doc)
        
        # Apply moderation action
        action_taken = await self._apply_moderation_action(
            user=user,
            action=action,
            reason=reason,
            duration_hours=duration_hours,
            reputation_change=reputation_change,
            admin_id=admin_id
        )
        
        # Update report
        await self.db.reports.update_one(
            {"id": report_id},
            {
                "$set": {
                    "status": ReportStatus.RESOLVED,
                    "action_taken": action_taken,
                    "admin_notes": reason,
                    "handled_by": admin_id,
                    "resolved_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Create audit log
        await self._create_audit_log(
            action=AuditLogAction.REPORT_RESOLVED,
            actor_user_id=admin_id,
            target_user_id=report.reported_user_id,
            details={
                "report_id": report_id,
                "moderation_action": action,
                "reason": reason,
                "action_taken": action_taken
            }
        )
        
        return True
    
    async def _apply_moderation_action(
        self,
        user: User,
        action: ModerationAction,
        reason: str,
        duration_hours: Optional[int] = None,
        reputation_change: Optional[int] = None,
        admin_id: str = None
    ) -> str:
        """Apply moderation action to user"""
        action_description = ""
        
        if action == ModerationAction.WARNING:
            # Send warning notification
            await self.notification_service.notify_warning_received(user.id, reason)
            action_description = f"Warning issued: {reason}"
            
        elif action == ModerationAction.STRIKE:
            # Add strike
            new_strikes = user.strikes + 1
            await self.db.users.update_one(
                {"id": user.id},
                {"$set": {"strikes": new_strikes, "updated_at": datetime.utcnow()}}
            )
            
            # Notify user
            await self.notification_service.notify_strike_received(user.id, reason, new_strikes)
            
            # Auto-ban if 5 strikes
            if new_strikes >= 5:
                await self._ban_user(user.id, permanent=True, reason="5 strikes accumulated")
                action_description = f"Strike issued ({new_strikes}/5) and user permanently banned: {reason}"
            else:
                action_description = f"Strike issued ({new_strikes}/5): {reason}"
                
        elif action == ModerationAction.REPUTATION_PENALTY:
            if reputation_change:
                old_reputation = user.reputation
                new_reputation = max(0, old_reputation + reputation_change)  # reputation_change should be negative
                
                await self.db.users.update_one(
                    {"id": user.id},
                    {"$set": {"reputation": new_reputation, "updated_at": datetime.utcnow()}}
                )
                
                # Notify user
                await self.notification_service.notify_reputation_changed(user.id, old_reputation, new_reputation)
                action_description = f"Reputation penalty applied ({reputation_change} points): {reason}"
            else:
                action_description = "No reputation change specified"
                
        elif action == ModerationAction.TEMPORARY_BAN:
            if duration_hours:
                await self._ban_user(user.id, permanent=False, duration_hours=duration_hours, reason=reason)
                action_description = f"Temporary ban ({duration_hours} hours): {reason}"
            else:
                action_description = "No duration specified for temporary ban"
                
        elif action == ModerationAction.PERMANENT_BAN:
            await self._ban_user(user.id, permanent=True, reason=reason)
            action_description = f"Permanent ban: {reason}"
            
        elif action == ModerationAction.DISMISS:
            action_description = f"Report dismissed: {reason}"
        
        return action_description
    
    async def _ban_user(self, user_id: str, permanent: bool = True, duration_hours: int = None, reason: str = ""):
        """Ban a user (temporary or permanent)"""
        ban_data = {
            "is_banned": True,
            "ban_reason": reason,
            "banned_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if not permanent and duration_hours:
            ban_data["ban_expires_at"] = datetime.utcnow() + timedelta(hours=duration_hours)
        else:
            ban_data["ban_expires_at"] = None  # Permanent ban
        
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": ban_data}
        )
        
        # Notify user
        await self.notification_service.create_notification_for_user(
            user_id=user_id,
            type="account_suspended",
            title="Compte suspendu",
            message=f"Votre compte a été {'temporairement' if not permanent else 'définitivement'} suspendu. Raison: {reason}",
            priority="urgent"
        )
    
    async def check_and_unban_users(self) -> int:
        """Check for expired temporary bans and unban users"""
        now = datetime.utcnow()
        
        # Find users with expired temporary bans
        expired_bans = await self.db.users.update_many(
            {
                "is_banned": True,
                "ban_expires_at": {"$lte": now, "$ne": None}
            },
            {
                "$set": {
                    "is_banned": False,
                    "ban_reason": None,
                    "banned_at": None,
                    "ban_expires_at": None,
                    "updated_at": now
                }
            }
        )
        
        return expired_bans.modified_count
    
    async def get_user_moderation_history(self, user_id: str) -> Dict[str, Any]:
        """Get moderation history for a user"""
        # Get reports against user
        reports_count = await self.db.reports.count_documents({"reported_user_id": user_id})
        
        # Get audit logs for user
        audit_logs = []
        async for log_doc in self.db.audit_logs.find({
            "target_user_id": user_id,
            "action": {"$in": ["moderation_action", "user_banned", "user_unbanned"]}
        }).sort("created_at", -1).limit(10):
            audit_logs.append(log_doc)
        
        # Get user current status
        user_doc = await self.db.users.find_one({"id": user_id})
        user = User(**user_doc) if user_doc else None
        
        return {
            "user_id": user_id,
            "reports_against": reports_count,
            "strikes": user.strikes if user else 0,
            "reputation": user.reputation if user else 0,
            "is_banned": getattr(user, 'is_banned', False) if user else False,
            "ban_reason": getattr(user, 'ban_reason', None) if user else None,
            "recent_actions": audit_logs
        }
    
    async def _create_audit_log(
        self,
        action: AuditLogAction,
        actor_user_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """Create audit log entry"""
        audit_log = AuditLog(
            action=action,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            target_type=target_type,
            target_id=target_id,
            details=details or {}
        )
        
        await self.db.audit_logs.insert_one(audit_log.dict())
        return audit_log
    
    async def get_moderation_stats(self) -> Dict[str, Any]:
        """Get moderation statistics"""
        # Reports by status
        reports_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        reports_by_status = {}
        async for doc in self.db.reports.aggregate(reports_pipeline):
            reports_by_status[doc["_id"]] = doc["count"]
        
        # Recent activity
        recent_reports = await self.db.reports.count_documents({
            "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
        })
        
        # Users with strikes
        users_with_strikes = await self.db.users.count_documents({"strikes": {"$gt": 0}})
        
        # Banned users
        banned_users = await self.db.users.count_documents({"is_banned": True})
        
        return {
            "reports_by_status": reports_by_status,
            "recent_reports_7d": recent_reports,
            "users_with_strikes": users_with_strikes,
            "banned_users": banned_users,
            "total_reports": sum(reports_by_status.values())
        }