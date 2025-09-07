from typing import Dict, Any

from verselink_api import VerselinkAPI as BaseVerselinkAPI


class VerselinkAPI(BaseVerselinkAPI):
    """Extended API client with event creation support."""

    async def create_event(self, org_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new event for an organization."""
        endpoint = f"/organizations/{org_id}/events"
        return await self._request("POST", endpoint, json=data)