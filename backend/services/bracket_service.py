from typing import Dict, List, Any, Optional
from models.tournament import Tournament, Match, Team, BracketNode, TournamentFormat
from database import get_database
import math

class BracketService:
    """Service for generating and managing tournament brackets"""
    
    def __init__(self):
        self.db = get_database()
    
    async def generate_bracket_visualization(self, tournament: Tournament) -> Dict[str, Any]:
        """Generate bracket visualization data"""
        if tournament.format == TournamentFormat.SINGLE_ELIMINATION:
            return await self._generate_se_bracket_visualization(tournament)
        elif tournament.format == TournamentFormat.DOUBLE_ELIMINATION:
            return await self._generate_de_bracket_visualization(tournament)
        elif tournament.format == TournamentFormat.ROUND_ROBIN:
            return await self._generate_rr_bracket_visualization(tournament)
        else:
            return {"format": tournament.format, "rounds": [], "matches": []}
    
    async def _generate_se_bracket_visualization(self, tournament: Tournament) -> Dict[str, Any]:
        """Generate single elimination bracket visualization"""
        # Get all matches for tournament
        matches = []
        async for match_doc in self.db.matches.find({"tournament_id": tournament.id}).sort("round", 1).sort("bracket_position", 1):
            matches.append(match_doc)
        
        # Get all teams
        teams = {}
        async for team_doc in self.db.teams.find({"tournament_id": tournament.id}):
            teams[team_doc["id"]] = team_doc
        
        # Organize matches by rounds
        rounds = {}
        for match in matches:
            round_num = match["round"]
            if round_num not in rounds:
                rounds[round_num] = []
            
            # Build match node
            node = BracketNode(
                match_id=match["id"],
                round=match["round"],
                position=match["bracket_position"],
                state=match["state"]
            )
            
            # Add team information
            if match["team_a_id"] and match["team_a_id"] in teams:
                team_a = teams[match["team_a_id"]]
                node.team_a = {
                    "id": team_a["id"],
                    "name": team_a["name"],
                    "seed": team_a.get("seed")
                }
            
            if match["team_b_id"] and match["team_b_id"] in teams:
                team_b = teams[match["team_b_id"]]
                node.team_b = {
                    "id": team_b["id"],
                    "name": team_b["name"],
                    "seed": team_b.get("seed")
                }
            
            # Add winner information
            if match["winner_team_id"] and match["winner_team_id"] in teams:
                winner = teams[match["winner_team_id"]]
                node.winner = {
                    "id": winner["id"],
                    "name": winner["name"]
                }
            
            # Add scores
            node.score_a = match.get("score_a")
            node.score_b = match.get("score_b")
            
            rounds[round_num].append(node.dict())
        
        # Calculate bracket structure
        bracket_structure = self._calculate_se_structure(tournament.team_count, tournament.rounds_total)
        
        return {
            "format": "single_elimination",
            "rounds": rounds,
            "structure": bracket_structure,
            "total_rounds": tournament.rounds_total,
            "current_round": tournament.current_round
        }
    
    def _calculate_se_structure(self, team_count: int, total_rounds: int) -> Dict[str, Any]:
        """Calculate single elimination bracket structure"""
        # Calculate matches per round
        matches_per_round = []
        current_teams = team_count
        
        for round_num in range(1, total_rounds + 1):
            matches_in_round = math.ceil(current_teams / 2)
            matches_per_round.append(matches_in_round)
            current_teams = matches_in_round
        
        return {
            "matches_per_round": matches_per_round,
            "total_matches": sum(matches_per_round)
        }
    
    async def _generate_de_bracket_visualization(self, tournament: Tournament) -> Dict[str, Any]:
        """Generate double elimination bracket visualization (simplified)"""
        # For now, return single elimination structure
        # TODO: Implement proper double elimination with winner/loser brackets
        return await self._generate_se_bracket_visualization(tournament)
    
    async def _generate_rr_bracket_visualization(self, tournament: Tournament) -> Dict[str, Any]:
        """Generate round robin bracket visualization"""
        # Get all matches
        matches = []
        async for match_doc in self.db.matches.find({"tournament_id": tournament.id}).sort("round", 1).sort("bracket_position", 1):
            matches.append(match_doc)
        
        # Get all teams with stats
        teams = []
        async for team_doc in self.db.teams.find({"tournament_id": tournament.id}).sort("points", -1).sort("wins", -1):
            teams.append(team_doc)
        
        # Organize matches by rounds
        rounds = {}
        for match in matches:
            round_num = match["round"]
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(match)
        
        # Calculate standings
        standings = []
        for i, team in enumerate(teams):
            standings.append({
                "position": i + 1,
                "team_id": team["id"],
                "team_name": team["name"],
                "wins": team["wins"],
                "losses": team["losses"],
                "points": team["points"],
                "win_percentage": team["wins"] / max(team["wins"] + team["losses"], 1)
            })
        
        return {
            "format": "round_robin",
            "rounds": rounds,
            "standings": standings,
            "total_rounds": tournament.rounds_total,
            "current_round": tournament.current_round
        }
    
    async def get_next_matches(self, tournament_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get next matches to be played"""
        matches = []
        
        # Get pending matches from current round
        async for match_doc in self.db.matches.find({
            "tournament_id": tournament_id,
            "state": "pending",
            "$and": [
                {"team_a_id": {"$ne": None}},
                {"team_b_id": {"$ne": None}}
            ]
        }).sort("round", 1).sort("bracket_position", 1).limit(limit):
            
            # Get team information
            team_a = await self.db.teams.find_one({"id": match_doc["team_a_id"]})
            team_b = await self.db.teams.find_one({"id": match_doc["team_b_id"]})
            
            match_info = {
                "match_id": match_doc["id"],
                "round": match_doc["round"],
                "team_a": {
                    "id": team_a["id"],
                    "name": team_a["name"]
                } if team_a else None,
                "team_b": {
                    "id": team_b["id"],
                    "name": team_b["name"]
                } if team_b else None,
                "scheduled_at": match_doc.get("scheduled_at")
            }
            
            matches.append(match_info)
        
        return matches
    
    async def get_tournament_progress(self, tournament_id: str) -> Dict[str, Any]:
        """Get tournament progress statistics"""
        # Count matches by state
        pipeline = [
            {"$match": {"tournament_id": tournament_id}},
            {"$group": {
                "_id": "$state",
                "count": {"$sum": 1}
            }}
        ]
        
        match_stats = {}
        async for stat in self.db.matches.aggregate(pipeline):
            match_stats[stat["_id"]] = stat["count"]
        
        total_matches = sum(match_stats.values())
        completed_matches = match_stats.get("verified", 0)
        
        return {
            "total_matches": total_matches,
            "completed_matches": completed_matches,
            "pending_matches": match_stats.get("pending", 0),
            "reported_matches": match_stats.get("reported", 0),
            "progress_percentage": (completed_matches / total_matches * 100) if total_matches > 0 else 0,
            "match_stats": match_stats
        }