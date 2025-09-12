import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class VerselinkAPI:
    def __init__(self):
        self.base_url = Config.VERSELINK_API_BASE
        self.headers = Config.get_headers()
        self.session = None
        self.max_retries = Config.API_MAX_RETRIES
        self.backoff_factor = Config.API_BACKOFF_FACTOR
        self.timeout = aiohttp.ClientTimeout(total=Config.API_TIMEOUT)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers, timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to VerseLink API"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(1, self.max_retries + 1):
            try:
                if not self.session:
                    self.session = aiohttp.ClientSession(headers=self.headers, timeout=self.timeout)

                async with self.session.request(method, url, **kwargs) as response:
                    response_data = await response.json()

                    if response.status >= 500:
                        raise Exception(f"API Error {response.status}: {response_data.get('detail', 'Unknown error')}")
                    if response.status >= 400:
                        logger.error(f"API Error {response.status}: {response_data}")
                        raise Exception(f"API Error {response.status}: {response_data.get('detail', 'Unknown error')}")

                    return response_data

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.max_retries:
                    logger.error(f"Connection error to VerseLink API: {e}")
                    raise Exception(f"Connection error to VerseLink API: {e}")
                delay = self.backoff_factor * (2 ** (attempt - 1))
                logger.warning(f"API request failed (attempt {attempt}/{self.max_retries}): {e}. Retrying in {delay}s")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
    
    # Bot Management
    async def verify_bot(self) -> Dict[str, Any]:
        """Verify bot with VerseLink API"""
        return await self._request('POST', '/discord/bot/verify')
    
    async def get_health(self) -> Dict[str, Any]:
        """Get Discord system health"""
        return await self._request('GET', '/discord/health')
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Discord system statistics"""
        return await self._request('GET', '/discord/stats')
    
    # Guild Management
    async def register_guild(self, guild_id: str, guild_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a Discord guild with VerseLink"""
        return await self._request('POST', f'/discord/bot/guild/{guild_id}/register', json=guild_data)
    
    async def get_guild_config(self, guild_id: str) -> Dict[str, Any]:
        """Get guild configuration"""
        return await self._request('GET', f'/discord/bot/guild/{guild_id}/config')
    
    async def update_guild_config(self, guild_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update guild configuration"""
        return await self._request('PUT', f'/discord/bot/guild/{guild_id}/config', json=config)
    
    # Announcements
    async def announce_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send event announcement"""
        return await self._request('POST', '/discord/announce/event', json=event_data)
    
    async def announce_tournament(self, tournament_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send tournament announcement"""
        return await self._request('POST', '/discord/announce/tournament', json=tournament_data)
    
    # Message Sync
    async def sync_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync message across guilds"""
        return await self._request('POST', '/discord/sync/message', json=message_data)
    
    # Reminders
    async def schedule_reminder(self, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a reminder"""
        return await self._request('POST', '/discord/reminders/schedule', json=reminder_data)
    
    async def cancel_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """Cancel a scheduled reminder"""
        return await self._request('DELETE', f'/discord/reminders/{reminder_id}')
    
    async def get_reminders(self, guild_id: str = None) -> List[Dict[str, Any]]:
        """Get scheduled reminders"""
        endpoint = '/discord/reminders'
        if guild_id:
            endpoint += f'?guild_id={guild_id}'
        return await self._request('GET', endpoint)
    
    # Jobs
    async def get_jobs(self) -> List[Dict[str, Any]]:
        """Get pending jobs"""
        return await self._request('GET', '/discord/jobs')
    
    async def process_job(self, job_id: str) -> Dict[str, Any]:
        """Process a specific job"""
        return await self._request('POST', f'/discord/jobs/{job_id}/process')
    
    async def process_all_jobs(self) -> Dict[str, Any]:
        """Process all pending jobs"""
        return await self._request('POST', '/discord/jobs/process')
    
    # Events & Tournaments
    async def get_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming events"""
        return await self._request('GET', f'/events?limit={limit}')
    
    async def get_event(self, event_id: str) -> Dict[str, Any]:
        """Get specific event details"""
        return await self._request('GET', f'/events/{event_id}')
    
    async def get_tournaments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get active tournaments"""
        return await self._request('GET', f'/tournaments?limit={limit}')
    
    async def get_tournament(self, tournament_id: str) -> Dict[str, Any]:
        """Get specific tournament details"""
        return await self._request('GET', f'/tournaments/{tournament_id}')
    
    async def get_tournament_bracket(self, tournament_id: str) -> Dict[str, Any]:
        """Get tournament bracket"""
        return await self._request('GET', f'/tournaments/{tournament_id}/bracket')
    
    # User Management
    async def join_event(self, event_id: str, user_id: str) -> Dict[str, Any]:
        """Join user to event"""
        return await self._request('POST', f'/events/{event_id}/join', json={'user_id': user_id})
    
    async def leave_event(self, event_id: str, user_id: str) -> Dict[str, Any]:
        """Remove user from event"""
        return await self._request('POST', f'/events/{event_id}/leave', json={'user_id': user_id})
    
    async def join_tournament(self, tournament_id: str, user_id: str) -> Dict[str, Any]:
        """Join user to tournament"""
        return await self._request('POST', f'/tournaments/{tournament_id}/join', json={'user_id': user_id})
    
    async def leave_tournament(self, tournament_id: str, user_id: str) -> Dict[str, Any]:
        """Remove user from tournament"""
        return await self._request('POST', f'/tournaments/{tournament_id}/leave', json={'user_id': user_id})
    
    # Organizations
    async def get_organizations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get organizations"""
        return await self._request('GET', f'/orgs?limit={limit}')
    
    async def get_organization(self, org_id: str) -> Dict[str, Any]:
        """Get specific organization"""
        return await self._request('GET', f'/orgs/{org_id}')
    
    # Moderation
    async def report_user(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Report a user"""
        return await self._request('POST', '/moderation/reports', json=report_data)
    
    async def check_message_content(self, content: str, user_id: str) -> Dict[str, Any]:
        """Check message for auto-moderation"""
        return await self._request('POST', '/auto-moderation/check-message', json={
            'content': content,
            'context': f'discord_user:{user_id}'
        })
    
    async def get_organization_discord_config(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Récupère la configuration Discord d'une organisation"""
        try:
            return await self._request('GET', f'/orgs/{org_id}/discord-config')
        except Exception as e:
            if "404" in str(e):
                return None
            logger.error(f"Error in get_organization_discord_config: {e}")
            return None
    
    async def update_organization_discord_config(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour la configuration Discord d'une organisation"""
        return await self._request('PUT', f'/orgs/{org_id}/discord-config', json=config)
    
    async def save_discord_message_mapping(self, mapping_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sauvegarde le mapping entre message Discord et événement"""
        return await self._request('POST', '/discord/message-mappings', json=mapping_data)
    
    async def get_discord_message_mapping(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le mapping d'un message Discord"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = self.get_headers()
                async with session.get(
                    f"{self.base_url}/discord/message-mappings/{message_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        response.raise_for_status()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in get_discord_message_mapping: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_discord_message_mapping: {e}")
            return None
    
    async def save_discord_tournament_mapping(self, mapping_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sauvegarde le mapping entre message Discord et tournoi"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = self.get_headers()
                async with session.post(
                    f"{self.base_url}/discord/tournament-mappings",
                    headers=headers,
                    json=mapping_data
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in save_discord_tournament_mapping: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in save_discord_tournament_mapping: {e}")
            raise e