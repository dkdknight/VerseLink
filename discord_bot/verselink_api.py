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
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to VerseLink API"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(headers=self.headers)
            
            async with self.session.request(method, url, **kwargs) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    logger.error(f"API Error {response.status}: {response_data}")
                    raise Exception(f"API Error {response.status}: {response_data.get('detail', 'Unknown error')}")
                
                return response_data
        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP Client Error: {e}")
            raise Exception(f"Connection error to VerseLink API: {e}")
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
    
    async def disconnect_guild(self, guild_id: str) -> Dict[str, Any]:
        """Disconnect guild from VerseLink"""
        return await self._request('DELETE', f'/discord/bot/guild/{guild_id}/disconnect')
    
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
        return await self._request('GET', f'/organizations?limit={limit}')
    
    async def get_organization(self, org_id: str) -> Dict[str, Any]:
        """Get specific organization"""
        return await self._request('GET', f'/organizations/{org_id}')
    
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