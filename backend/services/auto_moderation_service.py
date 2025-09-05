from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from database import get_database
from models.notification import (
    Report, ReportCreate, ReportType, NotificationType, NotificationPriority
)
from models.user import User
from services.notification_service import NotificationService
from services.moderation_service import ModerationService
import re
import asyncio
import logging

logger = logging.getLogger(__name__)

class AutoModerationService:
    def __init__(self):
        self.db = get_database()
        self.notification_service = NotificationService()
        self.moderation_service = ModerationService()
        
        # Auto-moderation configuration (can be stored in database later)
        self.config = {
            "enabled": True,  # Master toggle for auto-moderation
            "spam_detection": {
                "enabled": True,
                "max_duplicate_messages": 3,  # Max similar messages in time window
                "time_window_minutes": 5,
                "similarity_threshold": 0.8  # 80% similarity
            },
            "profanity_filter": {
                "enabled": True,
                "words": [
                    # Basic profanity list - can be extended
                    "fuck", "shit", "damn", "bitch", "asshole", "bastard",
                    "piss", "crap", "hell", "ass", "dick", "pussy", "cock",
                    # Gaming specific toxic words
                    "noob", "scrub", "trash", "garbage", "cancer", "retard",
                    "faggot", "nigger", "kys", "kill yourself",
                    # French profanity
                    "merde", "putain", "salope", "connard", "enculé", "fils de pute"
                ],
                "action": "warning"  # warning, strike, or ban
            },
            "harassment_detection": {
                "enabled": True,
                "max_reports_per_user": 3,  # Max reports against single user before auto-action
                "time_window_hours": 24,
                "action": "temporary_ban",
                "ban_duration_hours": 24
            },
            "excessive_reporting": {
                "enabled": True,
                "max_reports_per_hour": 5,  # Max reports a user can make per hour
                "action": "warning"
            }
        }
    
    async def get_auto_moderation_config(self) -> Dict[str, Any]:
        """Get auto-moderation configuration"""
        # In future, this could be stored in database per organization
        return self.config
    
    async def update_auto_moderation_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update auto-moderation configuration"""
        self.config.update(new_config)
        # In future, save to database
        return self.config
    
    async def toggle_auto_moderation(self, enabled: bool) -> bool:
        """Toggle auto-moderation on/off"""
        self.config["enabled"] = enabled
        logger.info(f"Auto-moderation {'enabled' if enabled else 'disabled'}")
        return enabled
    
    async def check_message_content(self, user_id: str, content: str, context: str = None) -> Optional[Dict[str, Any]]:
        """Check message content for auto-moderation violations"""
        if not self.config["enabled"]:
            return None
        
        violations = []
        
        # Check for profanity
        if self.config["profanity_filter"]["enabled"]:
            profanity_result = await self._check_profanity(content)
            if profanity_result:
                violations.append(profanity_result)
        
        # Check for spam (duplicate/similar messages)
        if self.config["spam_detection"]["enabled"]:
            spam_result = await self._check_spam(user_id, content)
            if spam_result:
                violations.append(spam_result)
        
        if violations:
            # Apply auto-moderation action
            await self._apply_auto_moderation_action(user_id, violations, context)
            return {
                "violations": violations,
                "action_taken": True
            }
        
        # Store message for spam detection
        await self._store_user_message(user_id, content)
        
        return None
    
    async def check_user_behavior(self, user_id: str, action_type: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Check user behavior patterns for auto-moderation"""
        if not self.config["enabled"]:
            return None
        
        violations = []
        
        # Check excessive reporting
        if action_type == "report_created" and self.config["excessive_reporting"]["enabled"]:
            excessive_result = await self._check_excessive_reporting(user_id)
            if excessive_result:
                violations.append(excessive_result)
        
        # Check harassment pattern (multiple reports against same user)
        if action_type == "report_created" and self.config["harassment_detection"]["enabled"]:
            if context and context.get("reported_user_id"):
                harassment_result = await self._check_harassment_pattern(context["reported_user_id"])
                if harassment_result:
                    violations.append(harassment_result)
        
        if violations:
            # Apply auto-moderation action
            await self._apply_auto_moderation_action(user_id, violations, f"{action_type}:{context}")
            return {
                "violations": violations,
                "action_taken": True
            }
        
        return None
    
    async def _check_profanity(self, content: str) -> Optional[Dict[str, Any]]:
        """Check content for profanity"""
        content_lower = content.lower()
        found_words = []
        
        for word in self.config["profanity_filter"]["words"]:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, content_lower):
                found_words.append(word)
        
        if found_words:
            return {
                "type": "profanity",
                "severity": "medium",
                "details": f"Profanity detected: {', '.join(found_words[:3])}{'...' if len(found_words) > 3 else ''}",
                "action": self.config["profanity_filter"]["action"],
                "found_words": found_words
            }
        
        return None
    
    async def _check_spam(self, user_id: str, content: str) -> Optional[Dict[str, Any]]:
        """Check for spam (duplicate/similar messages)"""
        # Get recent messages from user
        time_cutoff = datetime.utcnow() - timedelta(minutes=self.config["spam_detection"]["time_window_minutes"])
        
        cursor = self.db.user_messages.find({
            "user_id": user_id,
            "created_at": {"$gte": time_cutoff}
        }).sort("created_at", -1).limit(10)
        
        recent_messages = []
        async for msg in cursor:
            recent_messages.append(msg["content"])
        
        # Check for duplicates or very similar messages
        similar_count = 0
        for msg in recent_messages:
            similarity = self._calculate_similarity(content, msg)
            if similarity >= self.config["spam_detection"]["similarity_threshold"]:
                similar_count += 1
        
        if similar_count >= self.config["spam_detection"]["max_duplicate_messages"]:
            return {
                "type": "spam",
                "severity": "high",
                "details": f"Detected {similar_count} similar messages in {self.config['spam_detection']['time_window_minutes']} minutes",
                "action": "warning",
                "similar_count": similar_count
            }
        
        return None
    
    async def _check_excessive_reporting(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Check if user is making too many reports"""
        time_cutoff = datetime.utcnow() - timedelta(hours=1)
        
        report_count = await self.db.reports.count_documents({
            "reporter_user_id": user_id,
            "created_at": {"$gte": time_cutoff}
        })
        
        if report_count >= self.config["excessive_reporting"]["max_reports_per_hour"]:
            return {
                "type": "excessive_reporting",
                "severity": "medium",
                "details": f"Made {report_count} reports in the last hour",
                "action": self.config["excessive_reporting"]["action"],
                "report_count": report_count
            }
        
        return None
    
    async def _check_harassment_pattern(self, reported_user_id: str) -> Optional[Dict[str, Any]]:
        """Check if a user is being harassed (multiple reports)"""
        time_cutoff = datetime.utcnow() - timedelta(hours=self.config["harassment_detection"]["time_window_hours"])
        
        report_count = await self.db.reports.count_documents({
            "reported_user_id": reported_user_id,
            "created_at": {"$gte": time_cutoff},
            "status": {"$in": ["pending", "investigating"]}
        })
        
        if report_count >= self.config["harassment_detection"]["max_reports_per_user"]:
            return {
                "type": "harassment_pattern",
                "severity": "high",
                "details": f"User received {report_count} reports in {self.config['harassment_detection']['time_window_hours']} hours",
                "action": self.config["harassment_detection"]["action"],
                "ban_duration_hours": self.config["harassment_detection"]["ban_duration_hours"],
                "report_count": report_count,
                "target_user_id": reported_user_id
            }
        
        return None
    
    async def _apply_auto_moderation_action(self, user_id: str, violations: List[Dict[str, Any]], context: str = None):
        """Apply auto-moderation action based on violations"""
        try:
            # Determine the most severe action needed
            actions = [v.get("action", "warning") for v in violations]
            
            # Priority: ban > strike > warning
            if "temporary_ban" in actions or "permanent_ban" in actions:
                action = "temporary_ban"
                duration_hours = 24  # Default
                
                # Get duration from harassment detection if applicable
                for v in violations:
                    if v.get("ban_duration_hours"):
                        duration_hours = v["ban_duration_hours"]
                        break
            elif "strike" in actions:
                action = "strike"
                duration_hours = None
            else:
                action = "warning"
                duration_hours = None
            
            # Create violation summary
            violation_details = []
            for v in violations:
                violation_details.append(f"{v['type']}: {v['details']}")
            
            reason = f"Auto-modération - {'; '.join(violation_details)}"
            
            # For harassment pattern, apply action to reported user
            target_user_id = user_id
            for v in violations:
                if v.get("type") == "harassment_pattern" and v.get("target_user_id"):
                    target_user_id = v["target_user_id"]
                    break
            
            # Apply the action through ModerationService
            if action == "warning":
                await self.notification_service.notify_warning_received(target_user_id, reason)
            elif action == "strike":
                # Get user to update strikes
                user_doc = await self.db.users.find_one({"id": target_user_id})
                if user_doc:
                    user = User(**user_doc)
                    new_strikes = user.strikes + 1
                    
                    await self.db.users.update_one(
                        {"id": target_user_id},
                        {"$set": {"strikes": new_strikes, "updated_at": datetime.utcnow()}}
                    )
                    
                    await self.notification_service.notify_strike_received(target_user_id, reason, new_strikes)
                    
                    # Auto-ban if 5 strikes
                    if new_strikes >= 5:
                        await self._ban_user(target_user_id, permanent=True, reason="5 strikes (auto-modération)")
            elif action == "temporary_ban":
                await self._ban_user(target_user_id, permanent=False, duration_hours=duration_hours, reason=reason)
            
            # Log auto-moderation action
            await self._create_auto_moderation_log(target_user_id, action, reason, violations, context)
            
            logger.info(f"Auto-moderation action applied: {action} to user {target_user_id} - {reason}")
            
        except Exception as e:
            logger.error(f"Error applying auto-moderation action: {e}")
    
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
            type=NotificationType.ACCOUNT_SUSPENDED,
            title="Compte suspendu (Auto-modération)",
            message=f"Votre compte a été {'temporairement' if not permanent else 'définitivement'} suspendu automatiquement. Raison: {reason}",
            priority=NotificationPriority.URGENT
        )
    
    async def _store_user_message(self, user_id: str, content: str):
        """Store user message for spam detection"""
        await self.db.user_messages.insert_one({
            "user_id": user_id,
            "content": content[:500],  # Limit content length
            "created_at": datetime.utcnow()
        })
        
        # Clean up old messages (keep only last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        await self.db.user_messages.delete_many({
            "created_at": {"$lt": cutoff}
        })
    
    async def _create_auto_moderation_log(self, user_id: str, action: str, reason: str, violations: List[Dict[str, Any]], context: str = None):
        """Create log entry for auto-moderation action"""
        log_entry = {
            "id": f"auto_{datetime.utcnow().timestamp()}",
            "type": "auto_moderation",
            "user_id": user_id,
            "action": action,
            "reason": reason,
            "violations": violations,
            "context": context,
            "created_at": datetime.utcnow()
        }
        
        await self.db.auto_moderation_logs.insert_one(log_entry)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simple implementation)"""
        if text1 == text2:
            return 1.0
        
        # Simple similarity based on common words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def get_auto_moderation_stats(self) -> Dict[str, Any]:
        """Get auto-moderation statistics"""
        # Get logs from last 7 days
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        cursor = self.db.auto_moderation_logs.find({
            "created_at": {"$gte": cutoff}
        })
        
        stats = {
            "total_actions": 0,
            "actions_by_type": {},
            "violations_by_type": {},
            "recent_actions": []
        }
        
        async for log in cursor:
            stats["total_actions"] += 1
            
            action = log.get("action", "unknown")
            stats["actions_by_type"][action] = stats["actions_by_type"].get(action, 0) + 1
            
            for violation in log.get("violations", []):
                v_type = violation.get("type", "unknown")
                stats["violations_by_type"][v_type] = stats["violations_by_type"].get(v_type, 0) + 1
            
            if len(stats["recent_actions"]) < 10:
                stats["recent_actions"].append({
                    "action": log.get("action"),
                    "reason": log.get("reason"),
                    "created_at": log.get("created_at")
                })
        
        stats["config"] = self.config
        return stats