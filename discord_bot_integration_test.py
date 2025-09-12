#!/usr/bin/env python3
"""
VerseLink Discord Bot Integration Test
Tests the integration between Discord Bot and Backend API
"""

import sys
import os
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add discord_bot directory to path
sys.path.insert(0, '/app/discord_bot')

class DiscordBotIntegrationTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.backend_url = "http://localhost:8001"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    async def test_backend_api_health(self):
        """Test backend API health endpoints"""
        print("\n" + "="*60)
        print("TESTING BACKEND API HEALTH")
        print("="*60)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test main health endpoint
                async with session.get(f"{self.backend_url}/api/v1/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Backend Health Check", True, f"Status: {data.get('status', 'unknown')}")
                    else:
                        self.log_test("Backend Health Check", False, f"Status code: {response.status}")
                
                # Test Discord health endpoint
                async with session.get(f"{self.backend_url}/api/v1/discord/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Discord Health Check", True, f"Status: {data.get('status', 'unknown')}")
                    else:
                        self.log_test("Discord Health Check", False, f"Status code: {response.status}")
                
                # Test root endpoint
                async with session.get(f"{self.backend_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Root Endpoint", True, f"Message: {data.get('message', 'unknown')}")
                    else:
                        self.log_test("Root Endpoint", False, f"Status code: {response.status}")
                        
        except Exception as e:
            self.log_test("Backend API Health", False, f"Connection error: {str(e)}")

    async def test_discord_api_endpoints(self):
        """Test Discord-specific API endpoints"""
        print("\n" + "="*60)
        print("TESTING DISCORD API ENDPOINTS")
        print("="*60)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test Discord events health
                async with session.get(f"{self.backend_url}/api/v1/discord/events/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Discord Events Health", True, f"Status: {data.get('status', 'unknown')}")
                    else:
                        self.log_test("Discord Events Health", False, f"Status code: {response.status}")
                
                # Test Discord webhook endpoint (should accept POST)
                webhook_data = {
                    "event_type": "test",
                    "guild_id": "123456789012345678",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {"test": "data"}
                }
                
                async with session.post(f"{self.backend_url}/api/v1/discord/webhooks/incoming", 
                                      json=webhook_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Discord Webhook Endpoint", True, f"Response: {data}")
                    else:
                        self.log_test("Discord Webhook Endpoint", False, f"Status code: {response.status}")
                
                # Test Discord interactions endpoint (should handle PING)
                interaction_data = {
                    "type": 1,  # PING
                    "id": "test-interaction-id",
                    "application_id": "test-app-id"
                }
                
                async with session.post(f"{self.backend_url}/api/v1/discord/events/interactions", 
                                      json=interaction_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("type") == 1:  # PONG
                            self.log_test("Discord Interactions PING", True, "PONG response received")
                        else:
                            self.log_test("Discord Interactions PING", False, f"Unexpected response: {data}")
                    else:
                        self.log_test("Discord Interactions PING", False, f"Status code: {response.status}")
                        
        except Exception as e:
            self.log_test("Discord API Endpoints", False, f"Error: {str(e)}")

    async def test_events_api_integration(self):
        """Test events API that Discord bot would use"""
        print("\n" + "="*60)
        print("TESTING EVENTS API INTEGRATION")
        print("="*60)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test events listing (public endpoint)
                async with session.get(f"{self.backend_url}/api/v1/events/") as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            self.log_test("Events List API", True, f"Returned {len(data)} events")
                        else:
                            self.log_test("Events List API", False, "Response is not a list")
                    else:
                        self.log_test("Events List API", False, f"Status code: {response.status}")
                
                # Test events with filters (what Discord bot would use)
                async with session.get(f"{self.backend_url}/api/v1/events/?limit=5") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Events List with Limit", True, f"Returned {len(data)} events")
                    else:
                        self.log_test("Events List with Limit", False, f"Status code: {response.status}")
                
                # Test event types filter
                async with session.get(f"{self.backend_url}/api/v1/events/?type=raid") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Events Filter by Type", True, f"Raid events: {len(data)}")
                    else:
                        self.log_test("Events Filter by Type", False, f"Status code: {response.status}")
                        
        except Exception as e:
            self.log_test("Events API Integration", False, f"Error: {str(e)}")

    async def test_tournaments_api_integration(self):
        """Test tournaments API that Discord bot would use"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENTS API INTEGRATION")
        print("="*60)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test tournaments listing (public endpoint)
                async with session.get(f"{self.backend_url}/api/v1/tournaments/") as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            self.log_test("Tournaments List API", True, f"Returned {len(data)} tournaments")
                        else:
                            self.log_test("Tournaments List API", False, "Response is not a list")
                    else:
                        self.log_test("Tournaments List API", False, f"Status code: {response.status}")
                
                # Test tournaments with filters
                async with session.get(f"{self.backend_url}/api/v1/tournaments/?limit=5") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Tournaments List with Limit", True, f"Returned {len(data)} tournaments")
                    else:
                        self.log_test("Tournaments List with Limit", False, f"Status code: {response.status}")
                
                # Test tournament format filter
                async with session.get(f"{self.backend_url}/api/v1/tournaments/?format=se") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Tournaments Filter by Format", True, f"SE tournaments: {len(data)}")
                    else:
                        self.log_test("Tournaments Filter by Format", False, f"Status code: {response.status}")
                        
        except Exception as e:
            self.log_test("Tournaments API Integration", False, f"Error: {str(e)}")

    async def test_organizations_api_integration(self):
        """Test organizations API that Discord bot would use"""
        print("\n" + "="*60)
        print("TESTING ORGANIZATIONS API INTEGRATION")
        print("="*60)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test organizations listing (public endpoint)
                async with session.get(f"{self.backend_url}/api/v1/orgs/") as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            self.log_test("Organizations List API", True, f"Returned {len(data)} organizations")
                        else:
                            self.log_test("Organizations List API", False, "Response is not a list")
                    else:
                        self.log_test("Organizations List API", False, f"Status code: {response.status}")
                
                # Test organizations with search
                async with session.get(f"{self.backend_url}/api/v1/orgs/?query=test") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Organizations Search", True, f"Search results: {len(data)}")
                    else:
                        self.log_test("Organizations Search", False, f"Status code: {response.status}")
                        
        except Exception as e:
            self.log_test("Organizations API Integration", False, f"Error: {str(e)}")

    async def test_discord_bot_api_class(self):
        """Test Discord bot API class functionality"""
        print("\n" + "="*60)
        print("TESTING DISCORD BOT API CLASS")
        print("="*60)
        
        try:
            from verselink_api import VerselinkAPI
            
            # Test API class initialization and health check
            async with VerselinkAPI() as api:
                # Test health check
                health_response = await api.get_health()
                if isinstance(health_response, dict) and health_response.get('status'):
                    self.log_test("VerselinkAPI Health Check", True, f"Status: {health_response['status']}")
                else:
                    self.log_test("VerselinkAPI Health Check", False, "Invalid health response")
                
                # Test events retrieval
                try:
                    events = await api.get_events(limit=3)
                    if isinstance(events, list):
                        self.log_test("VerselinkAPI Get Events", True, f"Retrieved {len(events)} events")
                    else:
                        self.log_test("VerselinkAPI Get Events", False, "Events response is not a list")
                except Exception as e:
                    self.log_test("VerselinkAPI Get Events", False, f"Error: {str(e)}")
                
                # Test tournaments retrieval
                try:
                    tournaments = await api.get_tournaments(limit=3)
                    if isinstance(tournaments, list):
                        self.log_test("VerselinkAPI Get Tournaments", True, f"Retrieved {len(tournaments)} tournaments")
                    else:
                        self.log_test("VerselinkAPI Get Tournaments", False, "Tournaments response is not a list")
                except Exception as e:
                    self.log_test("VerselinkAPI Get Tournaments", False, f"Error: {str(e)}")
                
                # Test organizations retrieval
                try:
                    orgs = await api.get_organizations(limit=3)
                    if isinstance(orgs, list):
                        self.log_test("VerselinkAPI Get Organizations", True, f"Retrieved {len(orgs)} organizations")
                    else:
                        self.log_test("VerselinkAPI Get Organizations", False, "Organizations response is not a list")
                except Exception as e:
                    self.log_test("VerselinkAPI Get Organizations", False, f"Error: {str(e)}")
                    
        except Exception as e:
            self.log_test("Discord Bot API Class", False, f"Error: {str(e)}")

    async def test_interactive_session_persistence(self):
        """Test interactive session management"""
        print("\n" + "="*60)
        print("TESTING INTERACTIVE SESSION PERSISTENCE")
        print("="*60)
        
        try:
            from interactive_events import InteractiveSession, SessionManager
            
            # Test session creation and persistence
            manager = SessionManager()
            
            # Create multiple sessions
            session1 = manager.create_session("user1", "event")
            session2 = manager.create_session("user2", "tournament")
            
            # Add some data to sessions
            session1.data['title'] = "Test Event"
            session1.data['description'] = "Test Description"
            session2.data['name'] = "Test Tournament"
            
            # Test session retrieval
            retrieved1 = manager.get_session("user1")
            retrieved2 = manager.get_session("user2")
            
            if retrieved1 and retrieved1.data.get('title') == "Test Event":
                self.log_test("Session Persistence - Event", True, "Event session data persisted")
            else:
                self.log_test("Session Persistence - Event", False, "Event session data not persisted")
            
            if retrieved2 and retrieved2.data.get('name') == "Test Tournament":
                self.log_test("Session Persistence - Tournament", True, "Tournament session data persisted")
            else:
                self.log_test("Session Persistence - Tournament", False, "Tournament session data not persisted")
            
            # Test session cleanup
            manager.end_user_sessions("user1")
            ended_session = manager.get_session("user1")
            
            if ended_session is None:
                self.log_test("Session Cleanup", True, "Session properly ended")
            else:
                self.log_test("Session Cleanup", False, "Session not properly ended")
                
        except Exception as e:
            self.log_test("Interactive Session Persistence", False, f"Error: {str(e)}")

    async def test_date_parsing_functionality(self):
        """Test date parsing functionality for interactive creation"""
        print("\n" + "="*60)
        print("TESTING DATE PARSING FUNCTIONALITY")
        print("="*60)
        
        try:
            from tournament_handlers import TournamentCreationHandler
            from verselink_api import VerselinkAPI
            
            api = VerselinkAPI()
            handler = TournamentCreationHandler(api)
            
            # Test various date formats
            test_dates = [
                ("25/12/2025 20:30", "DD/MM/YYYY HH:MM format"),
                ("2025-12-25 20:30", "YYYY-MM-DD HH:MM format"),
            ]
            
            for date_str, description in test_dates:
                try:
                    parsed_date = handler.parse_date(date_str)
                    if parsed_date and hasattr(parsed_date, 'year'):
                        self.log_test(f"Date Parsing - {description}", True, f"Parsed: {parsed_date}")
                    else:
                        self.log_test(f"Date Parsing - {description}", False, "Invalid parsed date")
                except Exception as e:
                    self.log_test(f"Date Parsing - {description}", False, f"Parse error: {str(e)}")
                    
        except Exception as e:
            self.log_test("Date Parsing Functionality", False, f"Error: {str(e)}")

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting VerseLink Discord Bot Integration Tests")
        print("="*80)
        
        # Run all tests
        await self.test_backend_api_health()
        await self.test_discord_api_endpoints()
        await self.test_events_api_integration()
        await self.test_tournaments_api_integration()
        await self.test_organizations_api_integration()
        await self.test_discord_bot_api_class()
        await self.test_interactive_session_persistence()
        await self.test_date_parsing_functionality()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("INTEGRATION TEST SUMMARY")
        print("="*80)
        print(f"📊 Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        print(f"\n⏰ Completed at: {datetime.now().isoformat()}")

async def main():
    """Main test function"""
    tester = DiscordBotIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())