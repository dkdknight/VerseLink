from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from database import get_database
from models.tournament import (
    Tournament, TournamentCreate, TournamentUpdate,
    Team, TeamCreate, TeamMember,
    Match, MatchState, TournamentState, TournamentFormat,
    ScoreReport
)
from models.user import User
import re
import uuid
import math
from services.match_dispute_service import MatchDisputeService
from services.notification_service import NotificationService
from utils.permissions import EventPermissions

class TournamentService:
    def __init__(self):
        self.db = get_database()
        self.match_dispute_service = MatchDisputeService()
        self.notification_service = NotificationService()
    
    async def generate_slug(self, name: str, org_id: str) -> str:
        """Generate unique slug for tournament"""
        base_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        base_slug = re.sub(r'\s+', '-', base_slug.strip())
        base_slug = base_slug[:50]
        
        counter = 1
        slug = base_slug
        
        while await self.db.tournaments.find_one({"slug": slug}):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    async def create_tournament(self, tournament_data: TournamentCreate, org_id: str, user_id: str) -> Tournament:
        """Create new tournament"""
        slug = await self.generate_slug(tournament_data.name, org_id)
        
        tournament = Tournament(
            **tournament_data.dict(),
            slug=slug,
            org_id=org_id,
            created_by=user_id
        )
        
        await self.db.tournaments.insert_one(tournament.dict())
        
        # Update org tournament count
        await self.db.organizations.update_one(
            {"id": org_id},
            {"$inc": {"tournament_count": 1}}
        )
        
        return tournament
    
    async def get_tournament(self, tournament_id: str) -> Optional[Tournament]:
        """Get tournament by ID"""
        tournament_doc = await self.db.tournaments.find_one({"id": tournament_id})
        return Tournament(**tournament_doc) if tournament_doc else None
    
    async def get_tournament_by_slug(self, slug: str) -> Optional[Tournament]:
        """Get tournament by slug"""
        tournament_doc = await self.db.tournaments.find_one({"slug": slug})
        return Tournament(**tournament_doc) if tournament_doc else None
    
    async def update_tournament(self, tournament_id: str, update_data: TournamentUpdate) -> Optional[Tournament]:
        """Update tournament"""
        update_dict = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value
        
        if not update_dict:
            return await self.get_tournament(tournament_id)
        
        update_dict["updated_at"] = datetime.utcnow()
        
        await self.db.tournaments.update_one(
            {"id": tournament_id},
            {"$set": update_dict}
        )
        
        return await self.get_tournament(tournament_id)
    
    async def create_team(self, tournament_id: str, team_data: TeamCreate, captain_id: str) -> Team:
        """Create team for tournament"""
        # Check if tournament exists and is open for registration
        tournament = await self.get_tournament(tournament_id)
        if not tournament:
            raise ValueError("Tournament not found")
        
        if tournament.state != TournamentState.OPEN_REGISTRATION:
            raise ValueError("Tournament registration is not open")
        
        if tournament.team_count >= tournament.max_teams:
            raise ValueError("Tournament is full")
        
        # Check if user already has a team in this tournament
        existing_team = await self.db.teams.find_one({
            "tournament_id": tournament_id,
            "captain_user_id": captain_id
        })
        
        if existing_team:
            raise ValueError("You already have a team in this tournament")
        
        # Check if team name is unique in tournament
        existing_name = await self.db.teams.find_one({
            "tournament_id": tournament_id,
            "name": team_data.name
        })
        
        if existing_name:
            raise ValueError("Team name already taken in this tournament")
        
        # Create team
        team = Team(
            **team_data.dict(),
            tournament_id=tournament_id,
            captain_user_id=captain_id
        )
        
        await self.db.teams.insert_one(team.dict())
        
        # Add captain as team member
        member = TeamMember(
            team_id=team.id,
            user_id=captain_id,
            is_captain=True
        )
        await self.db.team_members.insert_one(member.dict())
        
        # Update tournament team count
        await self.db.tournaments.update_one(
            {"id": tournament_id},
            {"$inc": {"team_count": 1}}
        )
        
        return team

    async def join_team(self, team_id: str, user_id: str) -> bool:
        """Join a team in a tournament"""
        team_doc = await self.db.teams.find_one({"id": team_id})
        if not team_doc:
            raise ValueError("Team not found")

        team = Team(**team_doc)

        tournament = await self.get_tournament(team.tournament_id)
        if not tournament:
            raise ValueError("Tournament not found")

        if tournament.state != TournamentState.OPEN_REGISTRATION:
            raise ValueError("Tournament registration is not open")

        if team.member_count >= tournament.team_size:
            raise ValueError("Team is full")

        existing_membership = await self.db.team_members.find_one({
            "team_id": team_id,
            "user_id": user_id
        })
        if existing_membership:
            raise ValueError("User already in team")

        other_team_membership = await self.db.team_members.find_one({
            "user_id": user_id,
            "team_id": {
                "$in": [t["id"] async for t in self.db.teams.find({"tournament_id": team.tournament_id})]
            }
        })
        if other_team_membership:
            raise ValueError("User is already in a team for this tournament")

        member = TeamMember(team_id=team_id, user_id=user_id, is_captain=False)
        await self.db.team_members.insert_one(member.dict())

        await self.db.teams.update_one({"id": team_id}, {"$inc": {"member_count": 1}})

        return True
    
    async def add_team_member(self, team_id: str, user_id: str, requester_id: str) -> bool:
        """Add member to team (captain only)"""
        # Get team
        team_doc = await self.db.teams.find_one({"id": team_id})
        if not team_doc:
            raise ValueError("Team not found")
        
        team = Team(**team_doc)
        
        # Check if requester is captain
        if team.captain_user_id != requester_id:
            raise ValueError("Only team captain can add members")
        
        # Get tournament to check team size limit
        tournament = await self.get_tournament(team.tournament_id)
        if not tournament:
            raise ValueError("Tournament not found")
        
        # Check if team is full
        if team.member_count >= tournament.team_size:
            raise ValueError("Team is full")
        
        # Check if user is already in a team for this tournament
        existing_membership = await self.db.team_members.find_one({
            "user_id": user_id,
            "team_id": {
                "$in": [
                    t["id"] async for t in self.db.teams.find({"tournament_id": team.tournament_id})
                ]
            }
        })
        
        if existing_membership:
            raise ValueError("User is already in a team for this tournament")
        
        # Add member
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            is_captain=False
        )
        await self.db.team_members.insert_one(member.dict())
        
        # Update team member count
        await self.db.teams.update_one(
            {"id": team_id},
            {"$inc": {"member_count": 1}}
        )
        
        return True
    
    async def remove_team_member(self, team_id: str, user_id: str, requester_id: str) -> bool:
        """Remove member from team"""
        # Get team
        team_doc = await self.db.teams.find_one({"id": team_id})
        if not team_doc:
            raise ValueError("Team not found")
        
        team = Team(**team_doc)
        
        # Check permissions (captain or self)
        if team.captain_user_id != requester_id and user_id != requester_id:
            raise ValueError("Only team captain or the member themselves can remove members")
        
        # Cannot remove captain
        if user_id == team.captain_user_id:
            raise ValueError("Cannot remove team captain")
        
        # Remove member
        result = await self.db.team_members.delete_one({
            "team_id": team_id,
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise ValueError("Member not found")
        
        # Update team member count
        await self.db.teams.update_one(
            {"id": team_id},
            {"$inc": {"member_count": -1}}
        )
        
        return True
    
    async def start_tournament(self, tournament_id: str, user_id: str) -> bool:
        """Start tournament and generate bracket"""
        tournament = await self.get_tournament(tournament_id)
        if not tournament:
            raise ValueError("Tournament not found")
        
        if tournament.state != TournamentState.REGISTRATION_CLOSED:
            raise ValueError("Tournament must be in registration closed state to start")
        
        if tournament.team_count < 2:
            raise ValueError("Tournament needs at least 2 teams to start")
        
        # Generate bracket
        await self._generate_bracket(tournament)
        
        # Update tournament state
        await self.db.tournaments.update_one(
            {"id": tournament_id},
            {"$set": {
                "state": TournamentState.ONGOING,
                "current_round": 1,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return True
    
    async def _generate_bracket(self, tournament: Tournament):
        """Generate tournament bracket based on format"""
        if tournament.format == TournamentFormat.SINGLE_ELIMINATION:
            await self._generate_single_elimination_bracket(tournament)
        elif tournament.format == TournamentFormat.DOUBLE_ELIMINATION:
            await self._generate_double_elimination_bracket(tournament)
        elif tournament.format == TournamentFormat.ROUND_ROBIN:
            await self._generate_round_robin_bracket(tournament)
        else:
            raise ValueError(f"Tournament format {tournament.format} not supported yet")
    
    async def _generate_single_elimination_bracket(self, tournament: Tournament):
        """Generate single elimination bracket"""
        teams = []
        async for team_doc in self.db.teams.find({"tournament_id": tournament.id}):
            teams.append(Team(**team_doc))
        
        # Calculate number of rounds needed
        rounds_total = math.ceil(math.log2(len(teams)))
        
        # Update tournament with rounds total
        await self.db.tournaments.update_one(
            {"id": tournament.id},
            {"$set": {"rounds_total": rounds_total}}
        )
        
        # Seed teams (for now, random order - can be improved later)
        import random
        random.shuffle(teams)
        for i, team in enumerate(teams):
            await self.db.teams.update_one(
                {"id": team.id},
                {"$set": {"seed": i + 1}}
            )
        
        # Generate first round matches
        matches = []
        for i in range(0, len(teams), 2):
            team_a = teams[i]
            team_b = teams[i + 1] if i + 1 < len(teams) else None
            
            match = Match(
                tournament_id=tournament.id,
                round=1,
                bracket_position=len(matches),
                team_a_id=team_a.id,
                team_b_id=team_b.id if team_b else None
            )
            
            # If no opponent, team_a advances automatically
            if not team_b:
                match.winner_team_id = team_a.id
                match.state = MatchState.VERIFIED
            
            matches.append(match)
            await self.db.matches.insert_one(match.dict())
        
        # Generate subsequent rounds (empty matches to be filled as tournament progresses)
        current_matches = len(matches)
        for round_num in range(2, rounds_total + 1):
            next_round_matches = max(1, current_matches // 2)
            for i in range(next_round_matches):
                match = Match(
                    tournament_id=tournament.id,
                    round=round_num,
                    bracket_position=i
                )
                await self.db.matches.insert_one(match.dict())
            current_matches = next_round_matches
    
    async def _generate_double_elimination_bracket(self, tournament: Tournament):
        """Generate double elimination bracket - simplified version"""
        # For now, implement as single elimination
        # TODO: Implement proper double elimination with winner/loser brackets
        await self._generate_single_elimination_bracket(tournament)
    
    async def _generate_round_robin_bracket(self, tournament: Tournament):
        """Generate round robin bracket"""
        teams = []
        async for team_doc in self.db.teams.find({"tournament_id": tournament.id}):
            teams.append(Team(**team_doc))
        
        n_teams = len(teams)
        rounds_total = n_teams - 1
        
        # Update tournament with rounds total
        await self.db.tournaments.update_one(
            {"id": tournament.id},
            {"$set": {"rounds_total": rounds_total}}
        )
        
        # Generate all matches (each team plays every other team once)
        match_position = 0
        for round_num in range(1, rounds_total + 1):
            for i in range(n_teams // 2):
                if round_num % 2 == 1:
                    team_a_idx = i
                    team_b_idx = n_teams - 1 - i
                else:
                    team_a_idx = n_teams - 1 - i
                    team_b_idx = i
                
                # Rotate teams (except first team in single elimination style)
                if round_num > 1:
                    team_a_idx = (team_a_idx + round_num - 1) % n_teams
                    team_b_idx = (team_b_idx + round_num - 1) % n_teams
                
                if team_a_idx != team_b_idx:
                    match = Match(
                        tournament_id=tournament.id,
                        round=round_num,
                        bracket_position=match_position,
                        team_a_id=teams[team_a_idx].id,
                        team_b_id=teams[team_b_idx].id
                    )
                    await self.db.matches.insert_one(match.dict())
                    match_position += 1

    async def schedule_match(self, match_id: str, scheduled_at: datetime, requester_id: str) -> bool:
        """Propose or confirm a match time. Returns True when fully scheduled."""
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            raise ValueError("Match not found")

        match = Match(**match_doc)

        captain_ids = []
        if match.team_a_id:
            team_a = await self.db.teams.find_one({"id": match.team_a_id})
            if team_a:
                captain_ids.append(team_a.get("captain_user_id"))
        if match.team_b_id:
            team_b = await self.db.teams.find_one({"id": match.team_b_id})
            if team_b:
                captain_ids.append(team_b.get("captain_user_id"))

        if requester_id not in captain_ids:
            raise ValueError("Only team captains can schedule matches")

        pending_at = match_doc.get("pending_scheduled_at")
        confirmations = match_doc.get("schedule_confirmations", [])

        # First proposal or proposer updating their proposal
        if not pending_at:
            # Ensure only one proposal is recorded when teams propose simultaneously
            result = await self.db.matches.update_one(
                {"id": match_id, "pending_scheduled_at": None},
                {
                    "$set": {
                        "pending_scheduled_at": scheduled_at,
                        "schedule_confirmations": [requester_id],
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            if result.modified_count == 0:
                # Another proposal was recorded concurrently
                raise ValueError("Another schedule proposal is already pending")
            return False

        if pending_at != scheduled_at:
            # Only the original proposer can change the pending date
            if requester_id in confirmations:
                await self.db.matches.update_one(
                    {"id": match_id},
                    {
                        "$set": {
                            "pending_scheduled_at": scheduled_at,
                            "schedule_confirmations": [requester_id],
                            "updated_at": datetime.utcnow(),
                        }
                    },
                )
                return False
            raise ValueError("Another schedule proposal is pending. Please respond to it first")

        # Confirmation from the opposing captain

        if requester_id in confirmations:
            return False

        confirmations.append(requester_id)
        if len(confirmations) >= 2:
            await self.db.matches.update_one(
                {"id": match_id},
                {
                    "$set": {
                        "scheduled_at": scheduled_at,
                        "pending_scheduled_at": None,
                        "schedule_confirmations": [],
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return True
        await self.db.matches.update_one(
            {"id": match_id},
            {
                "$set": {
                    "schedule_confirmations": confirmations,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return False

    async def decline_match_schedule(self, match_id: str, requester_id: str) -> None:
        """Decline a pending match schedule proposal."""
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            raise ValueError("Match not found")

        match = Match(**match_doc)

        captain_ids = []
        if match.team_a_id:
            team_a = await self.db.teams.find_one({"id": match.team_a_id})
            if team_a:
                captain_ids.append(team_a.get("captain_user_id"))
        if match.team_b_id:
            team_b = await self.db.teams.find_one({"id": match.team_b_id})
            if team_b:
                captain_ids.append(team_b.get("captain_user_id"))

        if requester_id not in captain_ids:
            raise ValueError("Only team captains can decline schedules")

        if not match_doc.get("pending_scheduled_at"):
            raise ValueError("No schedule proposal to decline")

        await self.db.matches.update_one(
            {"id": match_id},
            {
                "$set": {
                    "pending_scheduled_at": None,
                    "schedule_confirmations": [],
                    "updated_at": datetime.utcnow(),
                }
            },
        )
    
    async def report_match_score(self, match_id: str, score_report: ScoreReport, reporter_id: str) -> bool:
        """Report match score"""
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            raise ValueError("Match not found")
        
        match = Match(**match_doc)
        
        # Get team docs
        team_a_doc = team_b_doc = None
        if match.team_a_id:
            team_a_doc = await self.db.teams.find_one({"id": match.team_a_id})
        if match.team_b_id:
            team_b_doc = await self.db.teams.find_one({"id": match.team_b_id})
        if not team_a_doc or not team_b_doc:
            raise ValueError("Match has no teams assigned")

        # Check if reporter is captain of one of the teams
        if team_a_doc.get("captain_user_id") == reporter_id:
            opponent_captain_id = team_b_doc.get("captain_user_id")
        elif team_b_doc.get("captain_user_id") == reporter_id:
            opponent_captain_id = team_a_doc.get("captain_user_id")
        else:
            raise ValueError("Only team captains can report scores")
        
        # Determine winner
        winner_team_id = match.team_a_id if score_report.score_a > score_report.score_b else match.team_b_id
        loser_team_id = match.team_b_id if score_report.score_a > score_report.score_b else match.team_a_id
        
        # First report
        if match.state == MatchState.PENDING:
            update_data = {
                "score_a": score_report.score_a,
                "score_b": score_report.score_b,
                "winner_team_id": winner_team_id,
                "loser_team_id": loser_team_id,
                "state": MatchState.REPORTED,
                "reported_by": reporter_id,
                "reported_at": datetime.utcnow(),
                "notes": score_report.notes,
                "updated_at": datetime.utcnow(),
            }

            await self.db.matches.update_one(
                {"id": match_id},
                {"$set": update_data},
            )

            # Notify opposing team captain
            if opponent_captain_id:
                await self.notification_service.notify_match_score_reported(
                    match.tournament_id, match_id, opponent_captain_id
                )

            return True

        raise ValueError("Match result already reported and awaiting confirmation")

    async def confirm_match_score(self, match_id: str, confirmer_id: str) -> bool:
        """Confirm a reported match score by the opposing team captain."""
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            raise ValueError("Match not found")

        match = Match(**match_doc)

        if match.state != MatchState.REPORTED:
            raise ValueError("Match must be reported before confirmation")

        if match.reported_by == confirmer_id:
            raise ValueError("Reporting team cannot confirm their own score")

        # Determine opposing captain
        team_a_doc = team_b_doc = None
        if match.team_a_id:
            team_a_doc = await self.db.teams.find_one({"id": match.team_a_id})
        if match.team_b_id:
            team_b_doc = await self.db.teams.find_one({"id": match.team_b_id})

        opponent_captain_id = None
        if team_a_doc and team_a_doc.get("captain_user_id") == match.reported_by:
            opponent_captain_id = team_b_doc.get("captain_user_id") if team_b_doc else None
        elif team_b_doc and team_b_doc.get("captain_user_id") == match.reported_by:
            opponent_captain_id = team_a_doc.get("captain_user_id") if team_a_doc else None

        if opponent_captain_id != confirmer_id:
            raise ValueError("Only the opposing team captain can confirm the score")

        await self.verify_match_result(match_id, confirmer_id)
        return True

    async def forfeit_match(self, match_id: str, winner_team_id: str, user: User, notes: Optional[str] = None) -> bool:
        """Force end a match when a team doesn't show up"""
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            raise ValueError("Match not found")

        tournament = await self.get_tournament(match_doc["tournament_id"])
        if not tournament:
            raise ValueError("Tournament not found")

        # Permission check
        can_edit = await EventPermissions.can_edit_event(user, tournament.org_id, tournament.created_by)
        if not can_edit:
            raise ValueError("Insufficient permissions")

        match = Match(**match_doc)

        if match.state not in [MatchState.PENDING, MatchState.REPORTED]:
            raise ValueError("Match result already finalized")

        if winner_team_id not in [match.team_a_id, match.team_b_id]:
            raise ValueError("Winner team not part of this match")

        loser_team_id = match.team_b_id if winner_team_id == match.team_a_id else match.team_a_id

        update_data = {
            "score_a": 1 if winner_team_id == match.team_a_id else 0,
            "score_b": 1 if winner_team_id == match.team_b_id else 0,
            "winner_team_id": winner_team_id,
            "loser_team_id": loser_team_id,
            "state": MatchState.REPORTED,
            "reported_by": user.id,
            "notes": notes or "Forfeit",
            "updated_at": datetime.utcnow(),
        }

        await self.db.matches.update_one({"id": match_id}, {"$set": update_data})

        await self.verify_match_result(match_id, user.id)

        return True
    
    async def verify_match_result(self, match_id: str, verifier_id: str) -> bool:
        """Verify match result (referee/admin only)"""
        match_doc = await self.db.matches.find_one({"id": match_id})
        if not match_doc:
            raise ValueError("Match not found")
        
        match = Match(**match_doc)
        
        if match.state != MatchState.REPORTED:
            raise ValueError("Match must be reported before verification")
        
        # Update match state
        await self.db.matches.update_one(
            {"id": match_id},
            {"$set": {
                "state": MatchState.VERIFIED,
                "verified_by": verifier_id,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Update team records
        if match.winner_team_id:
            await self.db.teams.update_one(
                {"id": match.winner_team_id},
                {"$inc": {"wins": 1, "points": 3}}  # 3 points for win
            )
        
        if match.loser_team_id:
            await self.db.teams.update_one(
                {"id": match.loser_team_id},
                {"$inc": {"losses": 1, "points": 1}}  # 1 point for participation
            )
        
        # Advance tournament if needed
        tournament = await self.get_tournament(match.tournament_id)
        if tournament:
            await self._advance_tournament(tournament, match)
        
        return True
    
    async def _advance_tournament(self, tournament: Tournament, completed_match: Match):
        """Advance tournament after match completion"""
        if tournament.format == TournamentFormat.SINGLE_ELIMINATION:
            await self._advance_single_elimination(tournament, completed_match)
        # TODO: Implement other formats
    
    async def _advance_single_elimination(self, tournament: Tournament, completed_match: Match):
        """Advance single elimination tournament"""
        if not completed_match.winner_team_id:
            return
        
        # Find next round match
        next_round = completed_match.round + 1
        next_position = completed_match.bracket_position // 2
        
        next_match_doc = await self.db.matches.find_one({
            "tournament_id": tournament.id,
            "round": next_round,
            "bracket_position": next_position
        })
        
        if next_match_doc:
            # Determine if winner goes to team_a or team_b slot
            if completed_match.bracket_position % 2 == 0:
                # Even bracket position -> team_a
                update_field = "team_a_id"
            else:
                # Odd bracket position -> team_b
                update_field = "team_b_id"
            
            await self.db.matches.update_one(
                {"id": next_match_doc["id"]},
                {"$set": {update_field: completed_match.winner_team_id}}
            )
        else:
            # This was the final match
            await self.db.tournaments.update_one(
                {"id": tournament.id},
                {"$set": {
                    "state": TournamentState.FINISHED,
                    "winner_team_id": completed_match.winner_team_id,
                    "updated_at": datetime.utcnow()
                }}
            )
    
    async def list_tournaments(self, filters: Dict[str, Any] = None, limit: int = 20, skip: int = 0) -> List[Tournament]:
        """List tournaments with filters"""
        query = filters or {}
        
        cursor = self.db.tournaments.find(query).skip(skip).limit(limit).sort("start_at_utc", 1)
        tournaments = []
        
        async for tournament_doc in cursor:
            tournaments.append(Tournament(**tournament_doc))
        
        return tournaments