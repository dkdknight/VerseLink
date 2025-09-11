import httpx
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decouple import config

from database import get_database
from models.discord_integration import (
    DiscordEvent, DiscordEventCreate, DiscordEventStatus, DiscordEventEntityType,
    InteractiveMessage, InteractionResponse, ComponentType, ButtonStyle,
    DiscordRoleMapping, DiscordChannelMapping, DiscordJob, DiscordJobCreate,
    JobType, JobStatus
)
from models.event import Event
from services.discord_service import DiscordService

class DiscordEventsService:
    """Service for managing Discord Guild Scheduled Events and interactions"""
    
    def __init__(self):
        self.db = get_database()
        self.discord_service = DiscordService()
        self.bot_token = config("DISCORD_BOT_TOKEN", default="")
        self.discord_api_base = "https://discord.com/api/v10"
        
    async def _make_discord_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                                    guild_id: Optional[str] = None) -> Dict[str, Any]:
        """Make authenticated request to Discord API"""
        if not self.bot_token:
            raise ValueError("Discord bot token not configured")
        
        url = f"{self.discord_api_base}/{endpoint}"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method.upper() == "PATCH":
                response = await client.patch(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 429:  # Rate limited
                retry_after = response.headers.get("Retry-After", 1)
                await asyncio.sleep(float(retry_after))
                return await self._make_discord_request(method, endpoint, data, guild_id)
            
            if response.status_code >= 400:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"error": response.text}
                raise Exception(f"Discord API error {response.status_code}: {error_data}")
            
            return response.json() if response.content else {}
    
    # Guild Scheduled Events Management
    async def create_discord_event(self, event_id: str, guild_id: str) -> DiscordEvent:
        """Create Discord scheduled event from VerseLink event"""
        # Get VerseLink event
        event_doc = await self.db.events.find_one({"id": event_id})
        if not event_doc:
            raise ValueError("VerseLink event not found")
        
        event = Event(**event_doc)
        
        # Check if Discord event already exists
        existing_discord_event = await self.db.discord_events.find_one({
            "verselink_event_id": event_id,
            "guild_id": guild_id
        })
        if existing_discord_event:
            return DiscordEvent(**existing_discord_event)
        
        # Calculate end time
        end_time = event.start_at_utc + timedelta(minutes=event.duration_minutes)
        
        # Prepare Discord event data
        discord_event_data = {
            "name": event.title[:100],  # Discord limit
            "description": event.description[:1000] if event.description else None,  # Discord limit
            "scheduled_start_time": event.start_at_utc.isoformat() + "Z",
            "scheduled_end_time": end_time.isoformat() + "Z",
            "privacy_level": 2,  # Guild only
            "entity_type": 3,  # External
            "entity_metadata": {
                "location": event.location or "VerseLink"
            }
        }
        
        # Create Discord scheduled event
        discord_response = await self._make_discord_request(
            "POST", 
            f"guilds/{guild_id}/scheduled-events",
            discord_event_data,
            guild_id
        )
        
        # Store in database
        discord_event = DiscordEvent(
            discord_event_id=discord_response["id"],
            guild_id=guild_id,
            verselink_event_id=event_id,
            name=discord_response["name"],
            description=discord_response.get("description"),
            scheduled_start_time=datetime.fromisoformat(discord_response["scheduled_start_time"].replace("Z", "+00:00")).replace(tzinfo=None),
            scheduled_end_time=datetime.fromisoformat(discord_response["scheduled_end_time"].replace("Z", "+00:00")).replace(tzinfo=None) if discord_response.get("scheduled_end_time") else None,
            entity_type=DiscordEventEntityType.EXTERNAL,
            entity_metadata=discord_response.get("entity_metadata", {}),
            status=DiscordEventStatus.SCHEDULED,
            creator_id=discord_response.get("creator_id"),
            user_count=discord_response.get("user_count", 0)
        )
        
        await self.db.discord_events.insert_one(discord_event.dict())
        
        # Update VerseLink event with Discord event ID
        await self.db.events.update_one(
            {"id": event_id},
            {"$addToSet": {"discord_events": discord_response["id"]}}
        )
        
        return discord_event
    
    async def update_discord_event(self, event_id: str, guild_id: str) -> Optional[DiscordEvent]:
        """Update Discord scheduled event from VerseLink event"""
        # Get VerseLink event
        event_doc = await self.db.events.find_one({"id": event_id})
        if not event_doc:
            raise ValueError("VerseLink event not found")
        
        event = Event(**event_doc)
        
        # Get Discord event
        discord_event_doc = await self.db.discord_events.find_one({
            "verselink_event_id": event_id,
            "guild_id": guild_id
        })
        if not discord_event_doc:
            return None
        
        discord_event = DiscordEvent(**discord_event_doc)
        
        # Calculate end time
        end_time = event.start_at_utc + timedelta(minutes=event.duration_minutes)
        
        # Prepare update data
        update_data = {
            "name": event.title[:100],
            "description": event.description[:1000] if event.description else None,
            "scheduled_start_time": event.start_at_utc.isoformat() + "Z",
            "scheduled_end_time": end_time.isoformat() + "Z",
            "entity_metadata": {
                "location": event.location or "VerseLink"
            }
        }
        
        # Handle state changes
        if event.state == "cancelled":
            update_data["status"] = int(DiscordEventStatus.CANCELLED)
        elif event.state == "completed":
            update_data["status"] = int(DiscordEventStatus.COMPLETED)
        
        # Update Discord scheduled event
        discord_response = await self._make_discord_request(
            "PATCH",
            f"guilds/{guild_id}/scheduled-events/{discord_event.discord_event_id}",
            update_data,
            guild_id
        )
        
        # Update database
        updated_discord_event = DiscordEvent(
            **discord_event.dict(),
            name=discord_response["name"],
            description=discord_response.get("description"),
            scheduled_start_time=datetime.fromisoformat(discord_response["scheduled_start_time"].replace("Z", "+00:00")).replace(tzinfo=None),
            scheduled_end_time=datetime.fromisoformat(discord_response["scheduled_end_time"].replace("Z", "+00:00")).replace(tzinfo=None) if discord_response.get("scheduled_end_time") else None,
            status=DiscordEventStatus(str(discord_response["status"])),
            user_count=discord_response.get("user_count", 0),
            updated_at=datetime.utcnow()
        )
        
        await self.db.discord_events.replace_one(
            {"id": discord_event.id},
            updated_discord_event.dict()
        )
        
        return updated_discord_event
    
    async def delete_discord_event(self, event_id: str, guild_id: str) -> bool:
        """Delete Discord scheduled event"""
        # Get Discord event
        discord_event_doc = await self.db.discord_events.find_one({
            "verselink_event_id": event_id,
            "guild_id": guild_id
        })
        if not discord_event_doc:
            return False
        
        discord_event = DiscordEvent(**discord_event_doc)
        
        try:
            # Delete from Discord
            await self._make_discord_request(
                "DELETE",
                f"guilds/{guild_id}/scheduled-events/{discord_event.discord_event_id}",
                guild_id=guild_id
            )
        except Exception as e:
            # Log error but continue with database cleanup
            print(f"Failed to delete Discord event: {e}")
        
        # Remove from database
        await self.db.discord_events.delete_one({"id": discord_event.id})
        
        # Update VerseLink event
        await self.db.events.update_one(
            {"id": event_id},
            {"$pull": {"discord_events": discord_event.discord_event_id}}
        )
        
        return True
    
    async def sync_event_attendees(self, event_id: str, guild_id: str) -> Dict[str, Any]:
        """Sync attendees between VerseLink and Discord event"""
        # Get Discord event
        discord_event_doc = await self.db.discord_events.find_one({
            "verselink_event_id": event_id,
            "guild_id": guild_id
        })
        if not discord_event_doc:
            return {"error": "Discord event not found"}
        
        discord_event = DiscordEvent(**discord_event_doc)
        
        # Get Discord event users
        discord_users = await self._make_discord_request(
            "GET",
            f"guilds/{guild_id}/scheduled-events/{discord_event.discord_event_id}/users",
            guild_id=guild_id
        )
        
        # Get VerseLink signups
        verselink_signups = []
        async for signup_doc in self.db.event_signups.find({"event_id": event_id}):
            verselink_signups.append(signup_doc)
        
        return {
            "discord_attendees": len(discord_users),
            "verselink_signups": len(verselink_signups),
            "discord_users": discord_users,
            "sync_completed": True
        }
    
    # Interactive Messages and Reactions
    async def create_signup_message(self, event_id: str, guild_id: str, channel_id: str) -> InteractiveMessage:
        """Create interactive signup message with buttons"""
        # Get VerseLink event
        event_doc = await self.db.events.find_one({"id": event_id})
        if not event_doc:
            raise ValueError("Event not found")
        
        event = Event(**event_doc)
        
        # Create embed
        embed = {
            "title": f"📅 {event.title}",
            "description": event.description[:2000],
            "color": 0x00ff88,  # Green
            "fields": [
                {
                    "name": "🕐 Date et Heure",
                    "value": f"<t:{int(event.start_at_utc.timestamp())}:F>",
                    "inline": True
                },
                {
                    "name": "⏱️ Durée",
                    "value": f"{event.duration_minutes} minutes",
                    "inline": True
                },
                {
                    "name": "👥 Participants",
                    "value": f"{event.signup_count}/{event.max_participants or '∞'}",
                    "inline": True
                }
            ],
            "footer": {
                "text": "VerseLink - Cliquez sur les boutons pour vous inscrire"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if event.location:
            embed["fields"].append({
                "name": "📍 Lieu",
                "value": event.location,
                "inline": True
            })
        
        # Create buttons
        components = [
            {
                "type": 1,  # Action Row
                "components": [
                    {
                        "type": 2,  # Button
                        "style": 3,  # Success (Green)
                        "label": "✅ S'inscrire",
                        "custom_id": f"signup_{event_id}",
                        "emoji": {"name": "📝"}
                    },
                    {
                        "type": 2,  # Button
                        "style": 4,  # Danger (Red)
                        "label": "❌ Se désinscrire",
                        "custom_id": f"withdraw_{event_id}",
                        "emoji": {"name": "🚫"}
                    },
                    {
                        "type": 2,  # Button
                        "style": 2,  # Secondary (Grey)
                        "label": "📊 Voir les inscrits",
                        "custom_id": f"view_signups_{event_id}",
                        "emoji": {"name": "👥"}
                    }
                ]
            }
        ]
        
        # Add role selection if event has roles
        event_roles = []
        async for role_doc in self.db.event_roles.find({"event_id": event_id}):
            event_roles.append(role_doc)
        
        if event_roles:
            role_options = []
            for role in event_roles[:25]:  # Discord limit
                role_options.append({
                    "label": role["name"],
                    "value": f"role_{role['id']}",
                    "description": role.get("description", "")[:100],
                    "emoji": {"name": "🎭"}
                })
            
            if role_options:
                components.append({
                    "type": 1,  # Action Row
                    "components": [
                        {
                            "type": 3,  # Select Menu
                            "custom_id": f"select_role_{event_id}",
                            "placeholder": "Choisir un rôle pour cet événement",
                            "options": role_options,
                            "min_values": 0,
                            "max_values": 1
                        }
                    ]
                })
        
        # Send message
        message_data = {
            "embeds": [embed],
            "components": components
        }
        
        discord_message = await self._make_discord_request(
            "POST",
            f"channels/{channel_id}/messages",
            message_data
        )
        
        # Store interactive message
        interactive_message = InteractiveMessage(
            guild_id=guild_id,
            channel_id=channel_id,
            discord_message_id=discord_message["id"],
            verselink_event_id=event_id,
            message_content=json.dumps(message_data),
            embed_data=embed,
            components=components,
            message_type="event_signup"
        )
        
        await self.db.interactive_messages.insert_one(interactive_message.dict())
        
        # Update event with message ID
        await self.db.events.update_one(
            {"id": event_id},
            {"$addToSet": {"discord_message_ids": discord_message["id"]}}
        )
        
        return interactive_message
    
    async def handle_signup_interaction(self, interaction_data: Dict[str, Any]) -> InteractionResponse:
        """Handle signup button/select interactions"""
        custom_id = interaction_data.get("data", {}).get("custom_id", "")
        user_id = interaction_data.get("member", {}).get("user", {}).get("id") or interaction_data.get("user", {}).get("id")
        guild_id = interaction_data.get("guild_id")
        
        if not user_id:
            return InteractionResponse(
                type=4,  # CHANNEL_MESSAGE_WITH_SOURCE
                data={
                    "content": "❌ Erreur: Impossible d'identifier l'utilisateur",
                    "flags": 64  # EPHEMERAL
                }
            )
        
        # Parse custom_id to get action and event_id
        parts = custom_id.split("_")
        if len(parts) < 2:
            return InteractionResponse(
                type=4,
                data={
                    "content": "❌ Erreur: Interaction invalide",
                    "flags": 64
                }
            )
        
        action = parts[0]
        event_id = "_".join(parts[1:])
        
        # Get user from database
        user_doc = await self.db.users.find_one({"discord_id": user_id})
        if not user_doc:
            return InteractionResponse(
                type=4,
                data={
                    "content": "❌ Vous devez d'abord vous connecter sur VerseLink avec votre compte Discord",
                    "flags": 64
                }
            )
        
        # Handle different actions
        if action == "signup":
            return await self._handle_signup_action(event_id, user_doc["id"], user_id)
        elif action == "withdraw":
            return await self._handle_withdraw_action(event_id, user_doc["id"], user_id)
        elif action == "view":
            return await self._handle_view_signups_action(event_id)
        elif action.startswith("role"):
            selected_role = interaction_data.get("data", {}).get("values", [None])[0]
            return await self._handle_role_selection(event_id, user_doc["id"], selected_role)
        else:
            return InteractionResponse(
                type=4,
                data={
                    "content": "❌ Action non reconnue",
                    "flags": 64
                }
            )
    
    async def _handle_signup_action(self, event_id: str, user_id: str, discord_id: str) -> InteractionResponse:
        """Handle signup button click"""
        # Check if already signed up
        existing_signup = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id
        })
        
        if existing_signup:
            return InteractionResponse(
                type=4,
                data={
                    "content": "ℹ️ Vous êtes déjà inscrit à cet événement",
                    "flags": 64
                }
            )
        
        # Get event details
        event_doc = await self.db.events.find_one({"id": event_id})
        if not event_doc:
            return InteractionResponse(
                type=4,
                data={
                    "content": "❌ Événement introuvable",
                    "flags": 64
                }
            )
        
        event = Event(**event_doc)
        
        # Check if event is full
        if event.max_participants and event.signup_count >= event.max_participants:
            signup_status = "waitlist"
            response_message = "📝 Vous avez été ajouté à la liste d'attente"
        else:
            signup_status = "confirmed"
            response_message = "✅ Inscription confirmée !"
        
        # Create signup
        from models.event import EventSignup, SignupStatus
        signup = EventSignup(
            event_id=event_id,
            user_id=user_id,
            status=SignupStatus.CONFIRMED if signup_status == "confirmed" else SignupStatus.WAITLIST,
            discord_notified=True
        )
        
        await self.db.event_signups.insert_one(signup.dict())
        
        # Update event counts
        if signup_status == "confirmed":
            await self.db.events.update_one(
                {"id": event_id},
                {"$inc": {"signup_count": 1, "confirmed_count": 1}}
            )
        else:
            await self.db.events.update_one(
                {"id": event_id},
                {"$inc": {"signup_count": 1}}
            )
        
        return InteractionResponse(
            type=4,
            data={
                "content": response_message,
                "flags": 64
            }
        )
    
    async def _handle_withdraw_action(self, event_id: str, user_id: str, discord_id: str) -> InteractionResponse:
        """Handle withdraw button click"""
        # Check if signed up
        existing_signup = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id
        })
        
        if not existing_signup:
            return InteractionResponse(
                type=4,
                data={
                    "content": "ℹ️ Vous n'êtes pas inscrit à cet événement",
                    "flags": 64
                }
            )
        
        # Update signup status
        await self.db.event_signups.update_one(
            {"id": existing_signup["id"]},
            {"$set": {"status": "withdrawn", "updated_at": datetime.utcnow()}}
        )
        
        # Update event counts
        if existing_signup["status"] == "confirmed":
            await self.db.events.update_one(
                {"id": event_id},
                {"$inc": {"signup_count": -1, "confirmed_count": -1}}
            )
        else:
            await self.db.events.update_one(
                {"id": event_id},
                {"$inc": {"signup_count": -1}}
            )
        
        return InteractionResponse(
            type=4,
            data={
                "content": "✅ Votre inscription a été annulée",
                "flags": 64
            }
        )
    
    async def _handle_view_signups_action(self, event_id: str) -> InteractionResponse:
        """Handle view signups button click"""
        # Get signups
        signups = []
        async for signup_doc in self.db.event_signups.find({
            "event_id": event_id,
            "status": {"$in": ["confirmed", "waitlist", "checked_in"]}
        }).limit(20):
            user_doc = await self.db.users.find_one({"id": signup_doc["user_id"]})
            if user_doc:
                signups.append({
                    "handle": user_doc["handle"],
                    "status": signup_doc["status"],
                    "role": signup_doc.get("role_id")
                })
        
        if not signups:
            content = "📭 Aucune inscription pour le moment"
        else:
            content = "👥 **Participants inscrits:**\n"
            for i, signup in enumerate(signups, 1):
                status_emoji = "✅" if signup["status"] == "confirmed" else "⏳" if signup["status"] == "waitlist" else "🎯"
                content += f"{i}. {status_emoji} {signup['handle']}\n"
            
            if len(signups) == 20:
                content += "\n_... et plus encore sur VerseLink_"
        
        return InteractionResponse(
            type=4,
            data={
                "content": content[:2000],  # Discord limit
                "flags": 64
            }
        )
    
    async def _handle_role_selection(self, event_id: str, user_id: str, selected_role: Optional[str]) -> InteractionResponse:
        """Handle role selection from dropdown"""
        if not selected_role or not selected_role.startswith("role_"):
            return InteractionResponse(
                type=4,
                data={
                    "content": "❌ Sélection de rôle invalide",
                    "flags": 64
                }
            )
        
        role_id = selected_role.replace("role_", "")
        
        # Check if user is signed up
        signup_doc = await self.db.event_signups.find_one({
            "event_id": event_id,
            "user_id": user_id
        })
        
        if not signup_doc:
            return InteractionResponse(
                type=4,
                data={
                    "content": "❌ Vous devez d'abord vous inscrire à l'événement",
                    "flags": 64
                }
            )
        
        # Get role details
        role_doc = await self.db.event_roles.find_one({"id": role_id})
        if not role_doc:
            return InteractionResponse(
                type=4,
                data={
                    "content": "❌ Rôle introuvable",
                    "flags": 64
                }
            )
        
        # Update signup with role
        await self.db.event_signups.update_one(
            {"id": signup_doc["id"]},
            {"$set": {"role_id": role_id, "updated_at": datetime.utcnow()}}
        )
        
        return InteractionResponse(
            type=4,
            data={
                "content": f"✅ Rôle **{role_doc['name']}** sélectionné !",
                "flags": 64
            }
        )
    
    # Job Processing Integration
    async def process_discord_event_jobs(self):
        """Process Discord event related jobs"""
        jobs = await self.db.discord_jobs.find({
            "status": JobStatus.PENDING,
            "job_type": {"$in": [JobType.CREATE_DISCORD_EVENT, JobType.UPDATE_DISCORD_EVENT, JobType.DELETE_DISCORD_EVENT]},
            "scheduled_at": {"$lte": datetime.utcnow()}
        }).to_list(10)
        
        for job_doc in jobs:
            job = DiscordJob(**job_doc)
            
            try:
                await self.db.discord_jobs.update_one(
                    {"id": job.id},
                    {"$set": {"status": JobStatus.PROCESSING, "started_at": datetime.utcnow()}}
                )
                
                result = None
                if job.job_type == JobType.CREATE_DISCORD_EVENT:
                    result = await self._process_create_event_job(job)
                elif job.job_type == JobType.UPDATE_DISCORD_EVENT:
                    result = await self._process_update_event_job(job)
                elif job.job_type == JobType.DELETE_DISCORD_EVENT:
                    result = await self._process_delete_event_job(job)
                
                await self.db.discord_jobs.update_one(
                    {"id": job.id},
                    {"$set": {
                        "status": JobStatus.COMPLETED,
                        "result": result,
                        "completed_at": datetime.utcnow()
                    }}
                )
                
            except Exception as e:
                error_msg = str(e)
                retry_count = job.retry_count + 1
                
                if retry_count >= job.max_retries:
                    await self.db.discord_jobs.update_one(
                        {"id": job.id},
                        {"$set": {
                            "status": JobStatus.FAILED,
                            "error_message": error_msg,
                            "completed_at": datetime.utcnow()
                        }}
                    )
                else:
                    # Reschedule with exponential backoff
                    retry_delay = 2 ** retry_count * 60  # Minutes
                    scheduled_at = datetime.utcnow() + timedelta(minutes=retry_delay)
                    
                    await self.db.discord_jobs.update_one(
                        {"id": job.id},
                        {"$set": {
                            "status": JobStatus.PENDING,
                            "retry_count": retry_count,
                            "scheduled_at": scheduled_at,
                            "error_message": error_msg,
                            "updated_at": datetime.utcnow()
                        }}
                    )
    
    async def _process_create_event_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process create Discord event job"""
        event_id = job.payload.get("event_id")
        guild_id = job.guild_id
        
        discord_event = await self.create_discord_event(event_id, guild_id)
        
        # Also create signup message if channel specified
        channel_id = job.payload.get("signup_channel_id")
        if channel_id:
            await self.create_signup_message(event_id, guild_id, channel_id)
        
        return {
            "discord_event_id": discord_event.discord_event_id,
            "status": "created"
        }
    
    async def _process_update_event_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process update Discord event job"""
        event_id = job.payload.get("event_id")
        guild_id = job.guild_id
        
        discord_event = await self.update_discord_event(event_id, guild_id)
        
        if discord_event:
            return {
                "discord_event_id": discord_event.discord_event_id,
                "status": "updated"
            }
        else:
            return {"status": "not_found"}
    
    async def _process_delete_event_job(self, job: DiscordJob) -> Dict[str, Any]:
        """Process delete Discord event job"""
        event_id = job.payload.get("event_id")
        guild_id = job.guild_id
        
        deleted = await self.delete_discord_event(event_id, guild_id)
        
        return {
            "status": "deleted" if deleted else "not_found"
        }