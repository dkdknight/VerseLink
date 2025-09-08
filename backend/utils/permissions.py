from typing import Optional
from models.user import User
from models.organization import OrgMemberRole
from typing import Any
from database import get_database

class EventPermissions:
    """Event permissions helper"""

    @staticmethod
    def _parse_member_role(role_value: Any) -> Optional[OrgMemberRole]:
        """Convert stored role values to OrgMemberRole enum."""
        if isinstance(role_value, OrgMemberRole):
            return role_value
        if isinstance(role_value, str):
            try:
                return OrgMemberRole(role_value.lower())
            except ValueError:
                return None
        return None
    
    @staticmethod
    async def can_create_event(user: User, org_id: str) -> bool:
        """Check if user can create events for organization"""
        if user.is_site_admin:
            return True
        
        # Check if user is org admin or staff
        db = get_database()
        member_doc = await db.org_members.find_one({
            "org_id": org_id,
            "user_id": user.id
        })
        
        if not member_doc:
            return False

        member_role = EventPermissions._parse_member_role(member_doc.get("role"))
        if not member_role:
            return False

        return member_role in (OrgMemberRole.ADMIN, OrgMemberRole.STAFF)
    
    @staticmethod
    async def can_edit_event(user: User, event_org_id: str, event_created_by: str) -> bool:
        """Check if user can edit event"""
        if user.is_site_admin:
            return True
        
        # Event creator can always edit their own events
        if event_created_by == user.id:
            return True
        
        # Org admins can edit any event in their org
        db = get_database()
        member_doc = await db.org_members.find_one({
            "org_id": event_org_id,
            "user_id": user.id
        })
        
        if member_doc:
            member_role = EventPermissions._parse_member_role(member_doc.get("role"))
            if member_role == OrgMemberRole.ADMIN:
                return True
        
        return False
    
    @staticmethod
    async def can_delete_event(user: User, event_org_id: str, event_created_by: str) -> bool:
        """Check if user can delete event"""
        # Same as edit permissions for now
        return await EventPermissions.can_edit_event(user, event_org_id, event_created_by)
    
    @staticmethod
    def can_view_event(user: Optional[User], event_visibility: str, event_org_id: str) -> bool:
        """Check if user can view event"""
        if event_visibility == "public":
            return True
        
        if not user:
            return False
        
        if user.is_site_admin:
            return True
        
        # For private/unlisted events, need to be a member of the org
        # This will be checked in the route handler
        return True  # Will be verified at route level