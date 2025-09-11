from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from database import get_database
from models.event import (
    Event, EventCreate, EventUpdate, EventSignup, EventSignupCreate,
    EventRole, EventRoleCreate, FleetShip, FleetShipCreate,
    SignupStatus, EventState
)
from models.user import User
from models.organization import Organization
import re
import uuid

class EventService:
    def __init__(self):
        self.db = get_database()
    
    async def generate_slug(self, title: str, org_id: str) -> str:
        """Generate unique slug for event"""
        # Create base slug from title
        base_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        base_slug = re.sub(r'\s+', '-', base_slug.strip())
        base_slug = base_slug[:50]  # Limit length
        
        # Check if slug exists
        counter = 1
        slug = base_slug
        
        while await self.db.events.find_one({"slug": slug}):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    async def create_event(self, event_data: EventCreate, org_id: str, user_id: str) -> Event:
        """Create new event"""
        # Generate slug
        slug = await self.generate_slug(event_data.title, org_id)
        
        # Create event
        event = Event(
            **event_data.dict(exclude={'roles', 'fleet_ships'}),
            slug=slug,
            org_id=org_id,
            created_by=user_id
        )
        
        # Insert event
        await self.db.events.insert_one(event.dict())
        
        # Create roles
        for role_data in event_data.roles:
            role = EventRole(**role_data.dict(), event_id=event.id)
            await self.db.event_roles.insert_one(role.dict())
        
        # Create fleet ships
        for ship_data in event_data.fleet_ships:
            ship = FleetShip(**ship_data.dict(), event_id=event.id)
            await self.db.fleet_ships.insert_one(ship.dict())
        
        # Update org event count
        await self.db.organizations.update_one(
            {"id": org_id},
            {"$inc": {"event_count": 1}}
        )
        
        # Trigger Discord integration if enabled
        if event.discord_integration_enabled:
            await self._trigger_discord_event_creation(event.id, org_id)
        
        return event
    
    async def get_event(self, event_id: str) -> Optional[Event]:
        """Get event by ID"""
        event_doc = await self.db.events.find_one({"id": event_id})
        return Event(**event_doc) if event_doc else None
    
    async def get_event_by_slug(self, slug: str) -> Optional[Event]:
        """Get event by slug"""
        event_doc = await self.db.events.find_one({"slug": slug})
        return Event(**event_doc) if event_doc else None
    
    async def update_event(self, event_id: str, update_data: EventUpdate) -> Optional[Event]:
        """Update event"""
        update_dict = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value
        
        if not update_dict:
            return await self.get_event(event_id)
        
        update_dict["updated_at"] = datetime.utcnow()
        
        await self.db.events.update_one(
            {"id": event_id},
            {"$set": update_dict}
        )
        
        # Trigger Discord integration update if enabled
        updated_event = await self.get_event(event_id)
        if updated_event and updated_event.discord_integration_enabled:
            await self._trigger_discord_event_update(event_id, updated_event.org_id)
        
        return updated_event
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete event and all related data"""
        # Delete related data
        await self.db.event_roles.delete_many({"event_id": event_id})
        await self.db.event_signups.delete_many({"event_id": event_id})
        await self.db.fleet_ships.delete_many({"event_id": event_id})
        
        # Delete event
        result = await self.db.events.delete_one({"id": event_id})
        return result.deleted_count > 0

    async def cancel_event(self, event_id: str) -> bool:
        """Mark an event as cancelled"""
        # Get event first to check Discord integration
        event = await self.get_event(event_id)
        
        result = await self.db.events.update_one(
            {"id": event_id},
            {"$set": {"state": EventState.CANCELLED, "updated_at": datetime.utcnow()}}
        )
        
        # Trigger Discord integration update if enabled
        if result.modified_count > 0 and event and event.discord_integration_enabled:
            await self._trigger_discord_event_update(event_id, event.org_id, action="cancelled")
        
        return result.modified_count > 0
    
    async def signup_for_event(self, event_id: str, user_id: str, signup_data: EventSignupCreate) -> EventSignup:
        """Sign up user for event"""
        # Check if already signed up
        banned_signup = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id,
            "status": SignupStatus.BANNED
        })
        if banned_signup:
            raise ValueError("User is banned from this event")

        existing_signup = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id,
            "status": {"$nin": [SignupStatus.WITHDRAWN, SignupStatus.KICKED, SignupStatus.BANNED]}
        })
        
        if existing_signup:
            raise ValueError("Already signed up for this event")

        # Check if user previously withdrew or was kicked so we can reuse the record
        rejoin_signup = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id,
            "status": {"$in": [SignupStatus.WITHDRAWN, SignupStatus.KICKED]},
        })
        
        # Get event
        event = await self.get_event(event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Check organization access
        if event.allowed_org_ids:
            user_org_ids = []
            async for doc in self.db.org_members.find({"user_id": user_id}):
                user_org_ids.append(doc["org_id"])
            if event.org_id not in user_org_ids and not any(org in event.allowed_org_ids for org in user_org_ids):
                raise ValueError("User not allowed to sign up for this event")

        # Check if event is open for signup
        if event.state != EventState.PUBLISHED:
            raise ValueError("Event is not open for signup")
        
        if event.start_at_utc <= datetime.utcnow():
            raise ValueError("Cannot signup for past events")
        
        # Determine initial status (confirmed or waitlist)
        status = SignupStatus.CONFIRMED
        position_in_waitlist = None
        
        # Check capacity if role specified
        if signup_data.role_id:
            role_doc = await self.db.event_roles.find_one({
                "id": signup_data.role_id,
                "event_id": event_id
            })
            
            if not role_doc:
                raise ValueError("Role not found")
            
            # Count current signups for this role
            current_signups = await self.db.event_signups.count_documents({
                "event_id": event_id,
                "role_id": signup_data.role_id,
                "status": {"$in": [SignupStatus.CONFIRMED, SignupStatus.CHECKED_IN]}
            })
            
            if current_signups >= role_doc["capacity"]:
                status = SignupStatus.WAITLIST
                # Get waitlist position
                waitlist_count = await self.db.event_signups.count_documents({
                    "event_id": event_id,
                    "role_id": signup_data.role_id,
                    "status": SignupStatus.WAITLIST
                })
                position_in_waitlist = waitlist_count + 1
        
        # Create or update signup
        signup_data_dict = signup_data.dict()
        if rejoin_signup:
            await self.db.event_signups.update_one(
                {"id": rejoin_signup["id"]},
                {"$set": {
                    **signup_data_dict,
                    "status": status,
                    "position_in_waitlist": position_in_waitlist,
                    "updated_at": datetime.utcnow(),
                    "created_at": datetime.utcnow(),
                }}
            )
            signup = EventSignup(
                id=rejoin_signup["id"],
                event_id=event_id,
                user_id=user_id,
                status=status,
                position_in_waitlist=position_in_waitlist,
                **signup_data_dict,
            )
        else:
            signup = EventSignup(
                **signup_data_dict,
                event_id=event_id,
                user_id=user_id,
                status=status,
                position_in_waitlist=position_in_waitlist
            )
            await self.db.event_signups.insert_one(signup.dict())
        
        # Update event signup count
        await self.db.events.update_one(
            {"id": event_id},
            {"$inc": {"signup_count": 1}}
        )
        
        if status == SignupStatus.CONFIRMED:
            await self.db.events.update_one(
                {"id": event_id},
                {"$inc": {"confirmed_count": 1}}
            )
        
        return signup
    
    async def _set_signup_status(self, event_id: str, user_id: str, new_status: SignupStatus) -> bool:
        """Update signup status for removal actions"""
        # Find signup
        signup_doc = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id,
            "status": {"$nin": [SignupStatus.WITHDRAWN, SignupStatus.KICKED, SignupStatus.BANNED]}
        })
        
        if not signup_doc:
            return False
        
        old_status = signup_doc["status"]
        
        await self.db.event_signups.update_one(
            {"id": signup_doc["id"]},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
        )
        
        # Update event counts
        await self.db.events.update_one(
            {"id": event_id},
            {"$inc": {"signup_count": -1}}
        )
        
        if old_status == SignupStatus.CONFIRMED:
            await self.db.events.update_one(
                {"id": event_id},
                {"$inc": {"confirmed_count": -1}}
            )
        elif old_status == SignupStatus.CHECKED_IN:
            await self.db.events.update_one(
                {"id": event_id},
                {"$inc": {"confirmed_count": -1, "checkin_count": -1}}
            )
        
        # Promote from waitlist if applicable
        if signup_doc.get("role_id") and old_status in [SignupStatus.CONFIRMED, SignupStatus.CHECKED_IN]:
            await self._promote_from_waitlist(event_id, signup_doc["role_id"])

        return True

    async def withdraw_from_event(self, event_id: str, user_id: str) -> bool:
        return await self._set_signup_status(event_id, user_id, SignupStatus.WITHDRAWN)

    async def kick_participant(self, event_id: str, user_id: str) -> bool:
        return await self._set_signup_status(event_id, user_id, SignupStatus.KICKED)

    async def ban_participant(self, event_id: str, user_id: str) -> bool:
        return await self._set_signup_status(event_id, user_id, SignupStatus.BANNED)

    async def unban_participant(self, event_id: str, user_id: str) -> bool:
        signup_doc = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id,
            "status": SignupStatus.BANNED
        })
        if not signup_doc:
            return False
        await self.db.event_signups.update_one(
            {"id": signup_doc["id"]},
            {"$set": {"status": SignupStatus.KICKED, "updated_at": datetime.utcnow()}}
        )
        
        return True
    
    async def checkin_for_event(self, event_id: str, user_id: str) -> bool:
        """Check in user for event"""
        # Get event
        event = await self.get_event(event_id)
        if not event:
            return False
        
        # Check if checkin is available (within 30 minutes of start)
        time_until_start = (event.start_at_utc - datetime.utcnow()).total_seconds() / 60
        if time_until_start > 30:
            raise ValueError("Check-in not yet available")
        
        if time_until_start < -15:  # 15 minutes after start
            raise ValueError("Check-in period has ended")
        
        # Find confirmed signup
        signup_doc = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id,
            "status": SignupStatus.CONFIRMED
        })
        
        if not signup_doc:
            return False
        
        # Update to checked in
        await self.db.event_signups.update_one(
            {"id": signup_doc["id"]},
            {"$set": {
                "status": SignupStatus.CHECKED_IN,
                "checked_in_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Update event checkin count
        await self.db.events.update_one(
            {"id": event_id},
            {"$inc": {"checkin_count": 1}}
        )
        
        return True
    
    async def _promote_from_waitlist(self, event_id: str, role_id: str):
        """Promote next person from waitlist to confirmed"""
        # Find next person in waitlist
        next_waitlist = await self.db.event_signups.find_one(
            {
                "event_id": event_id,
                "role_id": role_id,
                "status": SignupStatus.WAITLIST
            },
            sort=[("created_at", 1)]
        )
        
        if next_waitlist:
            await self.db.event_signups.update_one(
                {"id": next_waitlist["id"]},
                {"$set": {
                    "status": SignupStatus.CONFIRMED,
                    "position_in_waitlist": None,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Update event confirmed count
            await self.db.events.update_one(
                {"id": event_id},
                {"$inc": {"confirmed_count": 1}}
            )
    
    async def list_events(self, filters: Dict[str, Any] = None, limit: int = 20, skip: int = 0) -> List[Event]:
        """List events with filters"""
        query = filters or {}
        
        # Default filter: only published events
        if "state" not in query:
            query["state"] = EventState.PUBLISHED
        
        cursor = self.db.events.find(query).skip(skip).limit(limit).sort("start_at_utc", 1)
        events = []
        
        async for event_doc in cursor:
            events.append(Event(**event_doc))
        
        return events
    
    async def get_event_roles(self, event_id: str) -> List[EventRole]:
        """Get roles for event"""
        cursor = self.db.event_roles.find({"event_id": event_id})
        roles = []
        
        async for role_doc in cursor:
            roles.append(EventRole(**role_doc))
        
        return roles
    
    async def get_event_fleet(self, event_id: str) -> List[FleetShip]:
        """Get fleet ships for event"""
        cursor = self.db.fleet_ships.find({"event_id": event_id})
        ships = []
        
        async for ship_doc in cursor:
            ships.append(FleetShip(**ship_doc))
        
        return ships
    
    async def get_event_signups(self, event_id: str) -> List[EventSignup]:
        """Get signups for event"""
        cursor = self.db.event_signups.find({
            "event_id": event_id,
            "status": {"$nin": [SignupStatus.WITHDRAWN, SignupStatus.KICKED, SignupStatus.BANNED]}
        }).sort("created_at", 1)
        
        signups = []
        async for signup_doc in cursor:
            signups.append(EventSignup(**signup_doc))
        
        return signups