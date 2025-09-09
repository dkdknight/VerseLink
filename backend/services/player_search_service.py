from datetime import datetime
from typing import List, Optional, Dict, Any
from database import get_database
from models.tournament import (
    PlayerSearch, PlayerSearchCreate, PlayerSearchResponse,
    TournamentState
)
from models.user import User
import uuid

class PlayerSearchService:
    def __init__(self):
        self.db = get_database()
    
    async def create_player_search(self, tournament_id: str, search_data: PlayerSearchCreate, user_id: str) -> PlayerSearch:
        """Create or update a player search listing"""
        # Get tournament and verify it exists and is open for registration
        tournament_doc = await self.db.tournaments.find_one({"id": tournament_id})
        if not tournament_doc:
            raise ValueError("Tournament not found")
        
        if tournament_doc["state"] != TournamentState.OPEN_REGISTRATION:
            raise ValueError("Tournament registration is not open")
        
        # Check if user is already in a team for this tournament
        existing_membership = await self.db.team_members.find_one({
            "user_id": user_id,
            "team_id": {
                "$in": [
                    t["id"] async for t in self.db.teams.find({"tournament_id": tournament_id})
                ]
            }
        })
        
        if existing_membership:
            raise ValueError("You are already in a team for this tournament")
        
        # Check if user already has an active search for this tournament
        existing_search = await self.db.player_searches.find_one({
            "user_id": user_id,
            "tournament_id": tournament_id,
            "is_active": True
        })
        
        if existing_search:
            # Update existing search
            update_data = search_data.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            await self.db.player_searches.update_one(
                {"id": existing_search["id"]},
                {"$set": update_data}
            )
            
            # Return updated search
            updated_doc = await self.db.player_searches.find_one({"id": existing_search["id"]})
            return PlayerSearch(**updated_doc)
        else:
            # Create new search
            player_search = PlayerSearch(
                user_id=user_id,
                tournament_id=tournament_id,
                preferred_role=search_data.preferred_role,
                experience_level=search_data.experience_level,
                description=search_data.description
            )
            
            await self.db.player_searches.insert_one(player_search.dict())
            return player_search
    
    async def get_tournament_player_searches(self, tournament_id: str, limit: int = 20, skip: int = 0) -> List[PlayerSearchResponse]:
        """Get active player searches for a tournament"""
        # Verify tournament exists
        tournament_doc = await self.db.tournaments.find_one({"id": tournament_id})
        if not tournament_doc:
            raise ValueError("Tournament not found")
        
        searches = []
        
        # Build aggregation pipeline to get user info
        pipeline = [
            {
                "$match": {
                    "tournament_id": tournament_id,
                    "is_active": True,
                    "looking_for_team": True
                }
            },
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
                "$lookup": {
                    "from": "tournaments",
                    "localField": "tournament_id",
                    "foreignField": "id",
                    "as": "tournament"
                }
            },
            {"$unwind": "$tournament"},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        async for search_doc in self.db.player_searches.aggregate(pipeline):
            user = search_doc["user"]
            tournament = search_doc["tournament"]
            
            search_response = PlayerSearchResponse(
                id=search_doc["id"],
                user_id=search_doc["user_id"],
                user_handle=user["handle"],
                user_avatar_url=user.get("avatar_url"),
                tournament_id=search_doc["tournament_id"],
                tournament_name=tournament["name"],
                looking_for_team=search_doc["looking_for_team"],
                preferred_role=search_doc.get("preferred_role"),
                experience_level=search_doc.get("experience_level"),
                description=search_doc.get("description"),
                created_at=search_doc["created_at"],
                updated_at=search_doc["updated_at"]
            )
            
            searches.append(search_response)
        
        return searches
    
    async def get_user_player_searches(self, user_id: str) -> List[PlayerSearchResponse]:
        """Get all player searches for a user"""
        searches = []
        
        pipeline = [
            {"$match": {"user_id": user_id}},
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
                "$lookup": {
                    "from": "tournaments",
                    "localField": "tournament_id",
                    "foreignField": "id",
                    "as": "tournament"
                }
            },
            {"$unwind": "$tournament"},
            {"$sort": {"created_at": -1}}
        ]
        
        async for search_doc in self.db.player_searches.aggregate(pipeline):
            user = search_doc["user"]
            tournament = search_doc["tournament"]
            
            search_response = PlayerSearchResponse(
                id=search_doc["id"],
                user_id=search_doc["user_id"],
                user_handle=user["handle"],
                user_avatar_url=user.get("avatar_url"),
                tournament_id=search_doc["tournament_id"],
                tournament_name=tournament["name"],
                looking_for_team=search_doc["looking_for_team"],
                preferred_role=search_doc.get("preferred_role"),
                experience_level=search_doc.get("experience_level"),
                description=search_doc.get("description"),
                created_at=search_doc["created_at"],
                updated_at=search_doc["updated_at"]
            )
            
            searches.append(search_response)
        
        return searches
    
    async def update_player_search(self, search_id: str, search_data: PlayerSearchCreate, user_id: str) -> bool:
        """Update a player search (owner only)"""
        search_doc = await self.db.player_searches.find_one({"id": search_id})
        if not search_doc:
            raise ValueError("Player search not found")
        
        if search_doc["user_id"] != user_id:
            raise ValueError("Only the search owner can update this search")
        
        # Update search
        update_data = search_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await self.db.player_searches.update_one(
            {"id": search_id},
            {"$set": update_data}
        )
        
        return True
    
    async def deactivate_player_search(self, search_id: str, user_id: str) -> bool:
        """Deactivate a player search (owner only)"""
        search_doc = await self.db.player_searches.find_one({"id": search_id})
        if not search_doc:
            raise ValueError("Player search not found")
        
        if search_doc["user_id"] != user_id:
            raise ValueError("Only the search owner can deactivate this search")
        
        await self.db.player_searches.update_one(
            {"id": search_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        return True
    
    async def delete_player_search(self, search_id: str, user_id: str) -> bool:
        """Delete a player search (owner only)"""
        search_doc = await self.db.player_searches.find_one({"id": search_id})
        if not search_doc:
            raise ValueError("Player search not found")
        
        if search_doc["user_id"] != user_id:
            raise ValueError("Only the search owner can delete this search")
        
        await self.db.player_searches.delete_one({"id": search_id})
        return True
    
    async def cleanup_inactive_searches(self):
        """Cleanup searches for users who joined teams (called by scheduler)"""
        # Find all active searches
        active_searches = []
        async for search in self.db.player_searches.find({"is_active": True}):
            active_searches.append(search)
        
        # Check if users are still teamless
        for search in active_searches:
            user_id = search["user_id"]
            tournament_id = search["tournament_id"]
            
            # Check if user joined a team
            team_membership = await self.db.team_members.find_one({
                "user_id": user_id,
                "team_id": {
                    "$in": [
                        t["id"] async for t in self.db.teams.find({"tournament_id": tournament_id})
                    ]
                }
            })
            
            if team_membership:
                # User joined a team, deactivate search
                await self.db.player_searches.update_one(
                    {"id": search["id"]},
                    {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
                )
    
    async def search_players(self, tournament_id: str, role_filter: Optional[str] = None, experience_filter: Optional[str] = None, limit: int = 20, skip: int = 0) -> List[PlayerSearchResponse]:
        """Search for players with filters"""
        match_query = {
            "tournament_id": tournament_id,
            "is_active": True,
            "looking_for_team": True
        }
        
        if role_filter and role_filter.strip():
            match_query["preferred_role"] = {"$regex": role_filter.strip(), "$options": "i"}
        
        if experience_filter and experience_filter.strip():
            match_query["experience_level"] = {"$regex": experience_filter.strip(), "$options": "i"}
        
        searches = []
        
        pipeline = [
            {"$match": match_query},
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
                "$lookup": {
                    "from": "tournaments",
                    "localField": "tournament_id",
                    "foreignField": "id",
                    "as": "tournament"
                }
            },
            {"$unwind": "$tournament"},
            {"$sort": {"updated_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        async for search_doc in self.db.player_searches.aggregate(pipeline):
            user = search_doc["user"]
            tournament = search_doc["tournament"]
            
            search_response = PlayerSearchResponse(
                id=search_doc["id"],
                user_id=search_doc["user_id"],
                user_handle=user["handle"],
                user_avatar_url=user.get("avatar_url"),
                tournament_id=search_doc["tournament_id"],
                tournament_name=tournament["name"],
                looking_for_team=search_doc["looking_for_team"],
                preferred_role=search_doc.get("preferred_role"),
                experience_level=search_doc.get("experience_level"),
                description=search_doc.get("description"),
                created_at=search_doc["created_at"],
                updated_at=search_doc["updated_at"]
            )
            
            searches.append(search_response)
        
        return searches