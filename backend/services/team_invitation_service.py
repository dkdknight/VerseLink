from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from database import get_database
from models.tournament import (
    TeamInvitation, TeamInvitationCreate, TeamInvitationResponse,
    InvitationStatus, TournamentState
)
from models.user import User
from services.tournament_service import TournamentService
import uuid

class TeamInvitationService:
    def __init__(self):
        self.db = get_database()
        self.tournament_service = TournamentService()
    
    async def create_invitation(self, team_id: str, invitation_data: TeamInvitationCreate, captain_id: str) -> TeamInvitation:
        """Create a team invitation"""
        # Get team and verify captain
        team_doc = await self.db.teams.find_one({"id": team_id})
        if not team_doc:
            raise ValueError("Team not found")
        
        if team_doc["captain_user_id"] != captain_id:
            raise ValueError("Only team captain can send invitations")
        
        # Get tournament and verify state
        tournament = await self.tournament_service.get_tournament(team_doc["tournament_id"])
        if not tournament:
            raise ValueError("Tournament not found")
        
        if tournament.state != TournamentState.OPEN_REGISTRATION:
            raise ValueError("Tournament registration is not open")
        
        # Check if team is full
        if team_doc["member_count"] >= tournament.team_size:
            raise ValueError("Team is already full")
        
        # Find user by handle
        invited_user = await self.db.users.find_one({"handle": invitation_data.invited_user_handle})
        if not invited_user:
            raise ValueError("User not found")
        
        invited_user_id = invited_user["id"]
        
        # Check if user is already in a team for this tournament
        existing_membership = await self.db.team_members.find_one({
            "user_id": invited_user_id,
            "team_id": {
                "$in": [
                    t["id"] async for t in self.db.teams.find({"tournament_id": tournament.id})
                ]
            }
        })
        
        if existing_membership:
            raise ValueError("User is already in a team for this tournament")
        
        # Check if there's already a pending invitation for this user/team
        existing_invitation = await self.db.team_invitations.find_one({
            "team_id": team_id,
            "invited_user_id": invited_user_id,
            "status": InvitationStatus.PENDING
        })
        
        if existing_invitation:
            raise ValueError("There is already a pending invitation for this user")
        
        # Create invitation (expires in 7 days)
        invitation = TeamInvitation(
            team_id=team_id,
            tournament_id=tournament.id,
            invited_user_id=invited_user_id,
            invited_by=captain_id,
            message=invitation_data.message,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        await self.db.team_invitations.insert_one(invitation.dict())
        
        # TODO: Send notification to invited user
        
        return invitation
    
    async def respond_to_invitation(self, invitation_id: str, user_id: str, accept: bool) -> bool:
        """Respond to a team invitation"""
        invitation_doc = await self.db.team_invitations.find_one({"id": invitation_id})
        if not invitation_doc:
            raise ValueError("Invitation not found")
        
        invitation = TeamInvitation(**invitation_doc)
        
        # Verify the invitation is for this user
        if invitation.invited_user_id != user_id:
            raise ValueError("This invitation is not for you")
        
        # Check if invitation is still valid
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError("Invitation is no longer pending")
        
        if invitation.expires_at < datetime.utcnow():
            # Mark as expired
            await self.db.team_invitations.update_one(
                {"id": invitation_id},
                {"$set": {"status": InvitationStatus.EXPIRED}}
            )
            raise ValueError("Invitation has expired")
        
        # Update invitation status
        new_status = InvitationStatus.ACCEPTED if accept else InvitationStatus.DECLINED
        await self.db.team_invitations.update_one(
            {"id": invitation_id},
            {"$set": {
                "status": new_status,
                "responded_at": datetime.utcnow()
            }}
        )
        
        # If accepted, add user to team
        if accept:
            try:
                await self.tournament_service.add_team_member(
                    invitation.team_id, 
                    user_id, 
                    invitation.invited_by
                )
            except ValueError as e:
                # Revert invitation status if team join fails
                await self.db.team_invitations.update_one(
                    {"id": invitation_id},
                    {"$set": {"status": InvitationStatus.PENDING}}
                )
                raise e
        
        return True
    
    async def get_user_invitations(self, user_id: str, status: Optional[InvitationStatus] = None) -> List[TeamInvitationResponse]:
        """Get invitations for a user"""
        query = {"invited_user_id": user_id}
        if status:
            query["status"] = status.value
        
        invitations = []
        
        # Build aggregation pipeline to get team and tournament info
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "teams",
                    "localField": "team_id",
                    "foreignField": "id",
                    "as": "team"
                }
            },
            {"$unwind": "$team"},
            {
                "$lookup": {
                    "from": "tournaments",
                    "localField": "tournament_id",
                    "foreignField": "id",
                    "as": "tournament"
                }
            },
            {"$unwind": "$tournament"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "invited_by",
                    "foreignField": "id",
                    "as": "captain"
                }
            },
            {"$unwind": "$captain"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "invited_user_id",
                    "foreignField": "id",
                    "as": "invited_user"
                }
            },
            {"$unwind": "$invited_user"},
            {"$sort": {"created_at": -1}}
        ]
        
        async for invitation_doc in self.db.team_invitations.aggregate(pipeline):
            team = invitation_doc["team"]
            tournament = invitation_doc["tournament"]
            captain = invitation_doc["captain"]
            invited_user = invitation_doc["invited_user"]
            
            invitation_response = TeamInvitationResponse(
                id=invitation_doc["id"],
                team_id=invitation_doc["team_id"],
                team_name=team["name"],
                tournament_id=invitation_doc["tournament_id"],
                tournament_name=tournament["name"],
                invited_user_id=invitation_doc["invited_user_id"],
                invited_user_handle=invited_user["handle"],
                invited_by=invitation_doc["invited_by"],
                invited_by_handle=captain["handle"],
                status=invitation_doc["status"],
                message=invitation_doc.get("message"),
                created_at=invitation_doc["created_at"],
                expires_at=invitation_doc["expires_at"],
                responded_at=invitation_doc.get("responded_at")
            )
            
            invitations.append(invitation_response)
        
        return invitations
    
    async def get_team_invitations(self, team_id: str, user_id: str) -> List[TeamInvitationResponse]:
        """Get invitations sent by a team (captain only)"""
        # Verify user is team captain
        team_doc = await self.db.teams.find_one({"id": team_id})
        if not team_doc:
            raise ValueError("Team not found")
        
        if team_doc["captain_user_id"] != user_id:
            raise ValueError("Only team captain can view team invitations")
        
        return await self._get_team_invitations_data(team_id)
    
    async def _get_team_invitations_data(self, team_id: str) -> List[TeamInvitationResponse]:
        """Internal method to get team invitations with full data"""
        invitations = []
        
        pipeline = [
            {"$match": {"team_id": team_id}},
            {
                "$lookup": {
                    "from": "teams",
                    "localField": "team_id",
                    "foreignField": "id",
                    "as": "team"
                }
            },
            {"$unwind": "$team"},
            {
                "$lookup": {
                    "from": "tournaments",
                    "localField": "tournament_id",
                    "foreignField": "id",
                    "as": "tournament"
                }
            },
            {"$unwind": "$tournament"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "invited_by",
                    "foreignField": "id",
                    "as": "captain"
                }
            },
            {"$unwind": "$captain"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "invited_user_id",
                    "foreignField": "id",
                    "as": "invited_user"
                }
            },
            {"$unwind": "$invited_user"},
            {"$sort": {"created_at": -1}}
        ]
        
        async for invitation_doc in self.db.team_invitations.aggregate(pipeline):
            team = invitation_doc["team"]
            tournament = invitation_doc["tournament"]
            captain = invitation_doc["captain"]
            invited_user = invitation_doc["invited_user"]
            
            invitation_response = TeamInvitationResponse(
                id=invitation_doc["id"],
                team_id=invitation_doc["team_id"],
                team_name=team["name"],
                tournament_id=invitation_doc["tournament_id"],
                tournament_name=tournament["name"],
                invited_user_id=invitation_doc["invited_user_id"],
                invited_user_handle=invited_user["handle"],
                invited_by=invitation_doc["invited_by"],
                invited_by_handle=captain["handle"],
                status=invitation_doc["status"],
                message=invitation_doc.get("message"),
                created_at=invitation_doc["created_at"],
                expires_at=invitation_doc["expires_at"],
                responded_at=invitation_doc.get("responded_at")
            )
            
            invitations.append(invitation_response)
        
        return invitations
    
    async def cancel_invitation(self, invitation_id: str, user_id: str) -> bool:
        """Cancel a pending invitation (captain only)"""
        invitation_doc = await self.db.team_invitations.find_one({"id": invitation_id})
        if not invitation_doc:
            raise ValueError("Invitation not found")
        
        invitation = TeamInvitation(**invitation_doc)
        
        # Verify user is the captain who sent the invitation
        if invitation.invited_by != user_id:
            raise ValueError("Only the captain who sent the invitation can cancel it")
        
        # Check if invitation is still pending
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError("Can only cancel pending invitations")
        
        # Update invitation status
        await self.db.team_invitations.update_one(
            {"id": invitation_id},
            {"$set": {
                "status": InvitationStatus.DECLINED,  # Use declined to mark as canceled
                "responded_at": datetime.utcnow()
            }}
        )
        
        return True
    
    async def cleanup_expired_invitations(self):
        """Cleanup expired invitations (called by scheduler)"""
        await self.db.team_invitations.update_many(
            {
                "status": InvitationStatus.PENDING,
                "expires_at": {"$lt": datetime.utcnow()}
            },
            {"$set": {"status": InvitationStatus.EXPIRED}}
        )