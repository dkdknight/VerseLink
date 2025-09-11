from datetime import datetime
from typing import List, Optional, Dict, Any
from database import get_database
from models.tournament import (
    MatchDispute, MatchDisputeCreate, MatchDisputeResponse,
    DisputeStatus, MatchState
)
from models.user import User
import uuid

class MatchDisputeService:
    def __init__(self):
        self.db = get_database()
    
    async def create_dispute(self, match_id: str, dispute_data: MatchDisputeCreate, user_id: str) -> MatchDispute:
        """Create a match dispute"""
        # Get match and verify it exists
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            raise ValueError("Match not found")
        
        # Can only dispute reported matches
        if match_doc["state"] != MatchState.REPORTED:
            raise ValueError("Can only dispute matches awaiting confirmation")

        if match_doc.get("reported_by") == user_id:
            raise ValueError("Reporting team cannot dispute their own score")
        
        # Check if user is captain of one of the teams in the match
        user_is_captain = False
        if match_doc["team_a_id"]:
            team_a = await self.db.teams.find_one({"id": match_doc["team_a_id"]})
            if team_a and team_a["captain_user_id"] == user_id:
                user_is_captain = True
        
        if not user_is_captain and match_doc["team_b_id"]:
            team_b = await self.db.teams.find_one({"id": match_doc["team_b_id"]})
            if team_b and team_b["captain_user_id"] == user_id:
                user_is_captain = True
        
        if not user_is_captain:
            raise ValueError("Only team captains can dispute match results")
        
        # Check if there's already an open dispute for this match
        existing_dispute = await self.db.match_disputes.find_one({
            "match_id": match_id,
            "status": {"$in": [DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW]}
        })
        
        if existing_dispute:
            raise ValueError("There is already an active dispute for this match")
        
        # Create dispute
        dispute = MatchDispute(
            match_id=match_id,
            disputed_by=user_id,
            dispute_reason=dispute_data.dispute_reason
        )
        
        await self.db.match_disputes.insert_one(dispute.dict())
        
        # Update match state to disputed
        await self.db.matches.update_one(
            {"id": match_id},
            {"$set": {"state": MatchState.DISPUTED}}
        )
        
        return dispute
    
    async def get_dispute(self, dispute_id: str) -> Optional[MatchDisputeResponse]:
        """Get a dispute by ID with full details"""
        pipeline = [
            {"$match": {"id": dispute_id}},
            {
                "$lookup": {
                    "from": "matches",
                    "localField": "match_id",
                    "foreignField": "id",
                    "as": "match"
                }
            },
            {"$unwind": "$match"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "disputed_by",
                    "foreignField": "id",
                    "as": "disputer"
                }
            },
            {"$unwind": "$disputer"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "resolved_by",
                    "foreignField": "id",
                    "as": "resolver"
                }
            }
        ]
        
        dispute_doc = None
        async for doc in self.db.match_disputes.aggregate(pipeline):
            dispute_doc = doc
            break
        
        if not dispute_doc:
            return None
        
        # Get team names for match details
        match = dispute_doc["match"]
        match_details = {
            "id": match["id"],
            "round": match["round"],
            "team_a_name": None,
            "team_b_name": None,
            "score_a": match.get("score_a"),
            "score_b": match.get("score_b"),
            "state": match["state"]
        }
        
        if match["team_a_id"]:
            team_a = await self.db.teams.find_one({"id": match["team_a_id"]})
            if team_a:
                match_details["team_a_name"] = team_a["name"]
        
        if match["team_b_id"]:
            team_b = await self.db.teams.find_one({"id": match["team_b_id"]})
            if team_b:
                match_details["team_b_name"] = team_b["name"]
        
        disputer = dispute_doc["disputer"]
        resolver = dispute_doc.get("resolver")
        
        return MatchDisputeResponse(
            id=dispute_doc["id"],
            match_id=dispute_doc["match_id"],
            match_details=match_details,
            disputed_by=dispute_doc["disputed_by"],
            disputed_by_handle=disputer["handle"],
            dispute_reason=dispute_doc["dispute_reason"],
            status=dispute_doc["status"],
            admin_response=dispute_doc.get("admin_response"),
            resolved_by=dispute_doc.get("resolved_by"),
            resolved_by_handle=resolver[0]["handle"] if resolver else None,
            created_at=dispute_doc["created_at"],
            resolved_at=dispute_doc.get("resolved_at")
        )
    
    async def list_disputes(self, tournament_id: Optional[str] = None, status: Optional[DisputeStatus] = None, limit: int = 20, skip: int = 0) -> List[MatchDisputeResponse]:
        """List disputes with optional filters"""
        match_query = {}
        if tournament_id:
            match_query["tournament_id"] = tournament_id
        
        dispute_query = {}
        if status:
            dispute_query["status"] = status.value
        
        pipeline = [
            {"$match": dispute_query},
            {
                "$lookup": {
                    "from": "matches",
                    "localField": "match_id",
                    "foreignField": "id",
                    "as": "match"
                }
            },
            {"$unwind": "$match"}
        ]
        
        # Add tournament filter if specified
        if tournament_id:
            pipeline.append({"$match": {"match.tournament_id": tournament_id}})
        
        pipeline.extend([
            {
                "$lookup": {
                    "from": "users",
                    "localField": "disputed_by",
                    "foreignField": "id",
                    "as": "disputer"
                }
            },
            {"$unwind": "$disputer"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "resolved_by",
                    "foreignField": "id",
                    "as": "resolver"
                }
            },
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ])
        
        disputes = []
        
        async for dispute_doc in self.db.match_disputes.aggregate(pipeline):
            # Get team names for match details
            match = dispute_doc["match"]
            match_details = {
                "id": match["id"],
                "round": match["round"],
                "team_a_name": None,
                "team_b_name": None,
                "score_a": match.get("score_a"),
                "score_b": match.get("score_b"),
                "state": match["state"]
            }
            
            if match["team_a_id"]:
                team_a = await self.db.teams.find_one({"id": match["team_a_id"]})
                if team_a:
                    match_details["team_a_name"] = team_a["name"]
            
            if match["team_b_id"]:
                team_b = await self.db.teams.find_one({"id": match["team_b_id"]})
                if team_b:
                    match_details["team_b_name"] = team_b["name"]
            
            disputer = dispute_doc["disputer"]
            resolver = dispute_doc.get("resolver")
            
            dispute_response = MatchDisputeResponse(
                id=dispute_doc["id"],
                match_id=dispute_doc["match_id"],
                match_details=match_details,
                disputed_by=dispute_doc["disputed_by"],
                disputed_by_handle=disputer["handle"],
                dispute_reason=dispute_doc["dispute_reason"],
                status=dispute_doc["status"],
                admin_response=dispute_doc.get("admin_response"),
                resolved_by=dispute_doc.get("resolved_by"),
                resolved_by_handle=resolver[0]["handle"] if resolver else None,
                created_at=dispute_doc["created_at"],
                resolved_at=dispute_doc.get("resolved_at")
            )
            
            disputes.append(dispute_response)
        
        return disputes
    
    async def resolve_dispute(self, dispute_id: str, admin_id: str, admin_response: str, approve: bool) -> bool:
        """Resolve a dispute (admin only)"""
        # Get dispute
        dispute_doc = await self.db.match_disputes.find_one({"id": dispute_id})
        if not dispute_doc:
            raise ValueError("Dispute not found")
        
        dispute = MatchDispute(**dispute_doc)
        
        # Check if dispute is still open or under review
        if dispute.status not in [DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW]:
            raise ValueError("Dispute is already resolved")
        
        # TODO: Add admin permission check here
        # For now, assume any authenticated user can resolve disputes
        
        # Update dispute
        new_status = DisputeStatus.RESOLVED if approve else DisputeStatus.REJECTED
        await self.db.match_disputes.update_one(
            {"id": dispute_id},
            {"$set": {
                "status": new_status,
                "admin_response": admin_response,
                "resolved_by": admin_id,
                "resolved_at": datetime.utcnow()
            }}
        )
        
        # Update match state based on resolution
        match_doc = await self.db.matches.find_one({"id": dispute.match_id})
        if match_doc:
            if approve:
                # If dispute is approved, reset match to reported state for re-verification
                new_match_state = MatchState.REPORTED
            else:
                # If dispute is rejected, restore match to verified state
                new_match_state = MatchState.VERIFIED
            
            await self.db.matches.update_one(
                {"id": dispute.match_id},
                {"$set": {"state": new_match_state}}
            )
        
        return True
    
    async def set_dispute_under_review(self, dispute_id: str, admin_id: str) -> bool:
        """Mark dispute as under review (admin only)"""
        dispute_doc = await self.db.match_disputes.find_one({"id": dispute_id})
        if not dispute_doc:
            raise ValueError("Dispute not found")
        
        dispute = MatchDispute(**dispute_doc)
        
        if dispute.status != DisputeStatus.OPEN:
            raise ValueError("Can only set open disputes under review")
        
        await self.db.match_disputes.update_one(
            {"id": dispute_id},
            {"$set": {"status": DisputeStatus.UNDER_REVIEW}}
        )
        
        return True
    
    async def get_user_disputes(self, user_id: str) -> List[MatchDisputeResponse]:
        """Get disputes filed by a specific user"""
        return await self.list_disputes(status=None, limit=50, skip=0)  # TODO: Filter by user