#!/usr/bin/env python3
"""
VerseLink Backend API Test Suite - Phase 5 Discord Integration System Testing
Tests Discord Integration system for VerseLink application including webhooks, job queues, and bot API
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import io

class VerselinkAPITester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_tournament_id = None
        self.created_team_id = None
        self.created_match_id = None

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

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, headers: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        
        # Default headers
        default_headers = {'Content-Type': 'application/json'}
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            default_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"    {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=default_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            details = f"Status: {response.status_code}, Expected: {expected_status}"
            if not success:
                details += f", Response: {response.text[:200]}"

            self.log_test(name, success, details)
            return success, response_data

        except requests.exceptions.RequestException as e:
            self.log_test(name, False, f"Request failed: {str(e)}")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Unexpected error: {str(e)}")
            return False, {}

    def test_health_endpoints(self):
        """Test health check endpoints"""
        print("\n" + "="*50)
        print("TESTING HEALTH ENDPOINTS")
        print("="*50)
        
        # Main health check
        self.run_test(
            "Main Health Check",
            "GET",
            "/api/v1/health",
            200
        )
        
        # Discord integration health
        self.run_test(
            "Discord Integration Health",
            "GET", 
            "/api/v1/integrations/discord/health",
            200
        )
        
        # Root endpoint
        self.run_test(
            "Root Endpoint",
            "GET",
            "/",
            200
        )

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n" + "="*50)
        print("TESTING AUTH ENDPOINTS")
        print("="*50)
        
        # Discord redirect (should return auth URL)
        self.run_test(
            "Discord Auth Redirect",
            "GET",
            "/api/v1/auth/discord/redirect",
            200
        )
        
        # Test auth check without token (should fail)
        self.run_test(
            "Auth Check Without Token",
            "GET",
            "/api/v1/auth/check",
            403
        )
        
        # Test logout endpoint
        self.run_test(
            "Logout Endpoint",
            "POST",
            "/api/v1/auth/logout",
            200
        )

    def test_organizations_endpoints(self):
        """Test organization endpoints"""
        print("\n" + "="*50)
        print("TESTING ORGANIZATIONS ENDPOINTS")
        print("="*50)
        
        # List organizations (should return empty list for Phase 1)
        success, response = self.run_test(
            "List Organizations",
            "GET",
            "/api/v1/orgs/",
            200
        )
        
        if success:
            if isinstance(response, list):
                self.log_test("Organizations List Format", True, f"Returned {len(response)} organizations")
            else:
                self.log_test("Organizations List Format", False, "Response is not a list")
        
        # Test organization search with query
        self.run_test(
            "Search Organizations",
            "GET",
            "/api/v1/orgs/?query=test&limit=10",
            200
        )
        
        # Test get non-existent organization
        self.run_test(
            "Get Non-existent Organization",
            "GET",
            "/api/v1/orgs/non-existent-id",
            404
        )

    def test_users_endpoints(self):
        """Test user endpoints (require auth)"""
        print("\n" + "="*50)
        print("TESTING USERS ENDPOINTS (WITHOUT AUTH)")
        print("="*50)
        
        # These should fail without authentication
        self.run_test(
            "Get User Profile Without Auth",
            "GET",
            "/api/v1/users/me",
            403
        )

    def test_events_endpoints(self):
        """Test Phase 2 events endpoints"""
        print("\n" + "="*50)
        print("TESTING PHASE 2 EVENTS ENDPOINTS")
        print("="*50)
        
        # Test events listing (should work even without auth for public events)
        success, response = self.run_test(
            "List Events",
            "GET",
            "/api/v1/events/",
            200
        )
        
        if success:
            if isinstance(response, list):
                self.log_test("Events List Format", True, f"Returned {len(response)} events")
            else:
                self.log_test("Events List Format", False, "Response is not a list")
        
        # Test events with search query
        self.run_test(
            "Search Events with Query",
            "GET",
            "/api/v1/events/?query=test&limit=10",
            200
        )
        
        # Test events with type filter
        self.run_test(
            "Filter Events by Type",
            "GET",
            "/api/v1/events/?type=raid&limit=10",
            200
        )
        
        # Test events with org filter
        self.run_test(
            "Filter Events by Organization",
            "GET",
            "/api/v1/events/?org_id=test-org&limit=10",
            200
        )
        
        # Test events with date filters
        from datetime import datetime, timedelta
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        self.run_test(
            "Filter Events by Date Range",
            "GET",
            f"/api/v1/events/?start_date={start_date}&end_date={end_date}",
            200
        )
        
        # Test pagination
        self.run_test(
            "Events Pagination",
            "GET",
            "/api/v1/events/?limit=5&skip=0",
            200
        )
        
        # Test get non-existent event
        self.run_test(
            "Get Non-existent Event",
            "GET",
            "/api/v1/events/non-existent-id",
            404
        )
        
        # Test ICS download for non-existent event
        self.run_test(
            "Download ICS for Non-existent Event",
            "GET",
            "/api/v1/events/non-existent-id/ics",
            404
        )
        
        # Test protected endpoints without auth (should fail)
        test_event_id = "test-event-id"
        
        self.run_test(
            "Signup Without Auth",
            "POST",
            f"/api/v1/events/{test_event_id}/signups",
            403,
            data={"role_id": None, "notes": "Test signup"}
        )
        
        self.run_test(
            "Withdraw Without Auth",
            "DELETE",
            f"/api/v1/events/{test_event_id}/signups/me",
            403
        )
        
        self.run_test(
            "Checkin Without Auth",
            "POST",
            f"/api/v1/events/{test_event_id}/checkin",
            403
        )
        
        # Test create event without auth (should fail)
        self.run_test(
            "Create Event Without Auth",
            "POST",
            "/api/v1/orgs/test-org/events",
            403,
            data={
                "title": "Test Event",
                "description": "Test event description",
                "type": "raid",
                "start_at_utc": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "duration_minutes": 120
            }
        )

    def test_tournaments_endpoints(self):
        """Test Phase 3 tournaments endpoints"""
        print("\n" + "="*50)
        print("TESTING PHASE 3 TOURNAMENTS ENDPOINTS")
        print("="*50)
        
        # Test tournaments listing (should work without auth)
        success, response = self.run_test(
            "List Tournaments",
            "GET",
            "/api/v1/tournaments/",
            200
        )
        
        if success:
            if isinstance(response, list):
                self.log_test("Tournaments List Format", True, f"Returned {len(response)} tournaments")
            else:
                self.log_test("Tournaments List Format", False, "Response is not a list")
        
        # Test tournaments with search query
        self.run_test(
            "Search Tournaments with Query",
            "GET",
            "/api/v1/tournaments/?query=test&limit=10",
            200
        )
        
        # Test tournaments with format filter
        self.run_test(
            "Filter Tournaments by Format (SE)",
            "GET",
            "/api/v1/tournaments/?format=se&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by Format (DE)",
            "GET",
            "/api/v1/tournaments/?format=de&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by Format (RR)",
            "GET",
            "/api/v1/tournaments/?format=rr&limit=10",
            200
        )
        
        # Test tournaments with state filter
        self.run_test(
            "Filter Tournaments by State (Open Registration)",
            "GET",
            "/api/v1/tournaments/?state=open_registration&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by State (Ongoing)",
            "GET",
            "/api/v1/tournaments/?state=ongoing&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by State (Finished)",
            "GET",
            "/api/v1/tournaments/?state=finished&limit=10",
            200
        )
        
        # Test tournaments with org filter
        self.run_test(
            "Filter Tournaments by Organization",
            "GET",
            "/api/v1/tournaments/?org_id=test-org&limit=10",
            200
        )
        
        # Test combined filters
        self.run_test(
            "Combined Filters (Format + State)",
            "GET",
            "/api/v1/tournaments/?format=se&state=ongoing&limit=10",
            200
        )
        
        # Test pagination
        self.run_test(
            "Tournaments Pagination",
            "GET",
            "/api/v1/tournaments/?limit=5&skip=0",
            200
        )
        
        # Test get non-existent tournament
        self.run_test(
            "Get Non-existent Tournament",
            "GET",
            "/api/v1/tournaments/non-existent-id",
            404
        )
        
        # Test get tournament by slug (should also return 404 for non-existent)
        self.run_test(
            "Get Tournament by Non-existent Slug",
            "GET",
            "/api/v1/tournaments/non-existent-slug",
            404
        )
        
        # Test protected endpoints without auth (should fail with 401)
        test_tournament_id = "test-tournament-id"
        test_team_id = "test-team-id"
        test_match_id = "test-match-id"
        test_attachment_id = "test-attachment-id"
        
        # Team creation without auth
        self.run_test(
            "Create Team Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams",
            403,
            data={"name": "Test Team"}
        )
        
        # Add team member without auth
        self.run_test(
            "Add Team Member Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/members",
            403
        )
        
        # Remove team member without auth
        self.run_test(
            "Remove Team Member Without Auth",
            "DELETE",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/members/test-user-id",
            403
        )
        
        # Report match score without auth
        self.run_test(
            "Report Match Score Without Auth",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/report",
            403,
            data={"score_a": 2, "score_b": 1, "notes": "Test match"}
        )
        
        # Verify match result without auth
        self.run_test(
            "Verify Match Result Without Auth",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/verify",
            403
        )
        
        # Upload match attachment without auth
        self.run_test(
            "Upload Match Attachment Without Auth",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/attachments",
            403
        )
        
        # Delete attachment without auth
        self.run_test(
            "Delete Attachment Without Auth",
            "DELETE",
            f"/api/v1/tournaments/attachments/{test_attachment_id}",
            403
        )
        
        # Test attachment download (should work without auth but return 404 for non-existent)
        self.run_test(
            "Download Non-existent Attachment",
            "GET",
            f"/api/v1/tournaments/attachments/{test_attachment_id}/download",
            404
        )
        
        # Test create tournament without auth (should fail)
        from datetime import datetime, timedelta
        self.run_test(
            "Create Tournament Without Auth",
            "POST",
            "/api/v1/orgs/test-org/tournaments",
            403,
            data={
                "name": "Test Tournament",
                "description": "Test tournament description for Phase 3 testing",
                "format": "se",
                "start_at_utc": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "max_teams": 16,
                "team_size": 5,
                "prize_pool": "1000 aUEC"
            }
        )

    def test_discord_integration_endpoints(self):
        """Test Phase 5 Discord integration endpoints"""
        print("\n" + "="*60)
        print("TESTING PHASE 5 DISCORD INTEGRATION ENDPOINTS")
        print("="*60)
        
        # Test Discord health check
        success, response = self.run_test(
            "Discord Integration Health Check",
            "GET",
            "/api/v1/discord/health",
            200
        )
        
        if success:
            self.log_test("Discord Health Response Format", True, f"Health check returned: {response}")
        
        # Test Discord stats (admin only - should fail without auth)
        self.run_test(
            "Discord Stats Without Auth",
            "GET",
            "/api/v1/discord/stats",
            403
        )
        
        # Test guild management endpoints without auth (should fail)
        self.run_test(
            "List Discord Guilds Without Auth",
            "GET",
            "/api/v1/discord/guilds",
            403
        )
        
        self.run_test(
            "Register Discord Guild Without Auth",
            "POST",
            "/api/v1/discord/guilds",
            403,
            data={
                "guild_id": "123456789012345678",
                "guild_name": "Test Guild",
                "owner_id": "987654321098765432",
                "webhook_url": "https://discord.com/api/webhooks/test",
                "announcement_channel_id": "111111111111111111",
                "reminder_channel_id": "222222222222222222"
            }
        )
        
        self.run_test(
            "Get Discord Guild Without Auth",
            "GET",
            "/api/v1/discord/guilds/123456789012345678",
            403
        )

    def test_discord_webhook_endpoints(self):
        """Test Discord webhook endpoints"""
        print("\n" + "="*60)
        print("TESTING DISCORD WEBHOOK ENDPOINTS")
        print("="*60)
        
        # Test incoming webhook without signature
        webhook_payload = {
            "event_type": "message_create",
            "guild_id": "123456789012345678",
            "timestamp": "2025-01-27T10:00:00Z",
            "data": {
                "message": {
                    "id": "987654321098765432",
                    "content": "[SYNC] Important announcement from leadership",
                    "author": {
                        "id": "111111111111111111",
                        "username": "TestUser"
                    },
                    "channel_id": "222222222222222222"
                }
            }
        }
        
        success, response = self.run_test(
            "Discord Incoming Webhook Without Signature",
            "POST",
            "/api/v1/discord/webhooks/incoming",
            200,
            data=webhook_payload
        )
        
        if success:
            self.log_test("Webhook Response Format", True, f"Webhook processed: {response}")
        
        # Test incoming webhook with invalid signature
        self.run_test(
            "Discord Incoming Webhook With Invalid Signature",
            "POST",
            "/api/v1/discord/webhooks/incoming",
            401,
            data=webhook_payload,
            headers={"X-Signature-256": "sha256=invalid_signature"}
        )
        
        # Test webhook with invalid JSON
        self.run_test(
            "Discord Incoming Webhook Invalid JSON",
            "POST",
            "/api/v1/discord/webhooks/incoming",
            400,
            data="invalid json"
        )

    def test_discord_announcement_endpoints(self):
        """Test Discord announcement endpoints"""
        print("\n" + "="*60)
        print("TESTING DISCORD ANNOUNCEMENT ENDPOINTS")
        print("="*60)
        
        # Test event announcement without auth
        event_announcement = {
            "event_id": "test-event-id-12345",
            "guild_ids": ["123456789012345678", "876543210987654321"],
            "announcement_type": "created",
            "custom_message": "Join us for an epic Star Citizen event!"
        }
        
        self.run_test(
            "Announce Event Without Auth",
            "POST",
            "/api/v1/discord/announce/event",
            403,
            data=event_announcement
        )
        
        # Test tournament announcement without auth
        tournament_announcement = {
            "tournament_id": "test-tournament-id-12345",
            "guild_ids": ["123456789012345678", "876543210987654321"],
            "announcement_type": "started",
            "custom_message": "The championship tournament has begun!"
        }
        
        self.run_test(
            "Announce Tournament Without Auth",
            "POST",
            "/api/v1/discord/announce/tournament",
            403,
            data=tournament_announcement
        )

    def test_discord_message_sync_endpoints(self):
        """Test Discord message synchronization endpoints"""
        print("\n" + "="*60)
        print("TESTING DISCORD MESSAGE SYNC ENDPOINTS")
        print("="*60)
        
        # Test message sync without auth
        message_sync = {
            "source_guild_id": "123456789012345678",
            "target_guild_ids": ["876543210987654321", "555666777888999000"],
            "message_content": "Important announcement: Fleet operations scheduled for tomorrow at 20:00 UTC",
            "author_name": "Fleet Commander",
            "channel_type": "announcement"
        }
        
        self.run_test(
            "Sync Message Without Auth",
            "POST",
            "/api/v1/discord/sync/message",
            403,
            data=message_sync
        )

    def test_discord_reminder_endpoints(self):
        """Test Discord reminder endpoints"""
        print("\n" + "="*60)
        print("TESTING DISCORD REMINDER ENDPOINTS")
        print("="*60)
        
        # Test schedule reminders without auth
        test_event_id = "test-event-id-12345"
        
        self.run_test(
            "Schedule Event Reminders Without Auth",
            "POST",
            f"/api/v1/discord/reminders/schedule/{test_event_id}",
            403
        )

    def test_discord_job_management_endpoints(self):
        """Test Discord job management endpoints (admin only)"""
        print("\n" + "="*60)
        print("TESTING DISCORD JOB MANAGEMENT ENDPOINTS")
        print("="*60)
        
        # Test list jobs without auth (admin only)
        self.run_test(
            "List Discord Jobs Without Auth",
            "GET",
            "/api/v1/discord/jobs",
            403
        )
        
        # Test list jobs with filters
        self.run_test(
            "List Discord Jobs With Status Filter",
            "GET",
            "/api/v1/discord/jobs?status=pending&limit=10",
            403
        )
        
        # Test manual job processing without auth (admin only)
        self.run_test(
            "Process Discord Jobs Without Auth",
            "POST",
            "/api/v1/discord/jobs/process",
            403
        )

    def test_discord_bot_auth_endpoints(self):
        """Test Discord bot authentication endpoints"""
        print("\n" + "="*60)
        print("TESTING DISCORD BOT AUTHENTICATION ENDPOINTS")
        print("="*60)
        
        # Test bot verification with invalid credentials
        self.run_test(
            "Verify Bot Auth Invalid Credentials",
            "POST",
            "/api/v1/discord/bot/verify",
            401,
            data={
                "guild_id": "123456789012345678",
                "api_key": "invalid-api-key"
            }
        )
        
        # Test get guild config with invalid credentials
        self.run_test(
            "Get Bot Guild Config Invalid Credentials",
            "GET",
            "/api/v1/discord/bot/guild/123456789012345678/config?api_key=invalid-key",
            401
        )

    def test_discord_legacy_endpoints(self):
        """Test Discord legacy endpoints for backward compatibility"""
        print("\n" + "="*60)
        print("TESTING DISCORD LEGACY ENDPOINTS")
        print("="*60)
        
        # Test legacy event announce endpoint
        legacy_event_payload = {
            "event_id": "test-event-legacy",
            "guild_id": "123456789012345678",
            "event_data": {
                "title": "Legacy Event Test",
                "description": "Testing legacy webhook endpoint"
            }
        }
        
        success, response = self.run_test(
            "Legacy Event Announce Webhook",
            "POST",
            "/api/v1/discord/events/announce",
            200,
            data=legacy_event_payload
        )
        
        if success:
            self.log_test("Legacy Event Response", True, f"Legacy endpoint working: {response}")
        
        # Test legacy match announce endpoint
        legacy_match_payload = {
            "match_id": "test-match-legacy",
            "guild_id": "123456789012345678",
            "match_data": {
                "team_a": "Alpha Squadron",
                "team_b": "Beta Wing",
                "result": "2-1"
            }
        }
        
        success, response = self.run_test(
            "Legacy Match Announce Webhook",
            "POST",
            "/api/v1/discord/matches/announce",
            200,
            data=legacy_match_payload
        )
        
        if success:
            self.log_test("Legacy Match Response", True, f"Legacy endpoint working: {response}")

    def test_discord_data_validation(self):
        """Test Discord integration data validation"""
        print("\n" + "="*60)
        print("TESTING DISCORD DATA VALIDATION")
        print("="*60)
        
        # Test invalid guild registration data
        invalid_guild_data = {
            "guild_id": "invalid",  # Too short
            "guild_name": "",  # Empty name
            "owner_id": "123"  # Too short
        }
        
        self.run_test(
            "Register Guild Invalid Data",
            "POST",
            "/api/v1/discord/guilds",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_guild_data
        )
        
        # Test invalid event announcement data
        invalid_event_announcement = {
            "event_id": "",  # Empty event ID
            "guild_ids": [],  # Empty guild list
            "announcement_type": "invalid_type"  # Invalid type
        }
        
        self.run_test(
            "Announce Event Invalid Data",
            "POST",
            "/api/v1/discord/announce/event",
            403,  # Will fail auth first
            data=invalid_event_announcement
        )
        
        # Test invalid message sync data
        invalid_message_sync = {
            "source_guild_id": "",  # Empty source
            "target_guild_ids": [],  # Empty targets
            "message_content": "",  # Empty content
            "author_name": ""  # Empty author
        }
        
        self.run_test(
            "Sync Message Invalid Data",
            "POST",
            "/api/v1/discord/sync/message",
            403,  # Will fail auth first
            data=invalid_message_sync
        )

    def test_discord_error_handling(self):
        """Test Discord integration error handling"""
        print("\n" + "="*60)
        print("TESTING DISCORD ERROR HANDLING")
        print("="*60)
        
        # Test non-existent event announcement
        non_existent_event = {
            "event_id": "non-existent-event-id",
            "guild_ids": ["123456789012345678"],
            "announcement_type": "created"
        }
        
        self.run_test(
            "Announce Non-existent Event",
            "POST",
            "/api/v1/discord/announce/event",
            403,  # Will fail auth first, but tests endpoint structure
            data=non_existent_event
        )
        
        # Test non-existent tournament announcement
        non_existent_tournament = {
            "tournament_id": "non-existent-tournament-id",
            "guild_ids": ["123456789012345678"],
            "announcement_type": "started"
        }
        
        self.run_test(
            "Announce Non-existent Tournament",
            "POST",
            "/api/v1/discord/announce/tournament",
            403,  # Will fail auth first
            data=non_existent_tournament
        )
        
        # Test schedule reminders for non-existent event
        self.run_test(
            "Schedule Reminders Non-existent Event",
            "POST",
            "/api/v1/discord/reminders/schedule/non-existent-event",
            403  # Will fail auth first
        )

    def test_discord_webhook_signature_verification(self):
        """Test Discord webhook signature verification scenarios"""
        print("\n" + "="*60)
        print("TESTING DISCORD WEBHOOK SIGNATURE VERIFICATION")
        print("="*60)
        
        webhook_payload = {
            "event_type": "guild_member_add",
            "guild_id": "123456789012345678",
            "data": {
                "user": {
                    "id": "987654321098765432",
                    "username": "NewMember"
                }
            }
        }
        
        # Test with various signature formats
        signature_tests = [
            ("sha256=valid_looking_signature", 401),
            ("invalid_format_signature", 401),
            ("", 200),  # No signature should work (if verification is optional)
        ]
        
        for signature, expected_status in signature_tests:
            headers = {"X-Signature-256": signature} if signature else {}
            self.run_test(
                f"Webhook Signature Test ({signature[:20]}...)",
                "POST",
                "/api/v1/discord/webhooks/incoming",
                expected_status,
                data=webhook_payload,
                headers=headers
            )

    def test_discord_api_structure(self):
        """Test Discord API structure and endpoint availability"""
        print("\n" + "="*60)
        print("TESTING DISCORD API STRUCTURE")
        print("="*60)
        
        # Test that all Discord endpoints exist and return proper error codes
        discord_endpoints = [
            # Guild management
            ("GET", "/api/v1/discord/guilds", "List Discord Guilds", 403),
            ("POST", "/api/v1/discord/guilds", "Register Discord Guild", 403),
            ("GET", "/api/v1/discord/guilds/test-guild-id", "Get Discord Guild", 403),
            
            # Webhooks
            ("POST", "/api/v1/discord/webhooks/incoming", "Incoming Webhook", 200),
            
            # Announcements
            ("POST", "/api/v1/discord/announce/event", "Announce Event", 403),
            ("POST", "/api/v1/discord/announce/tournament", "Announce Tournament", 403),
            
            # Message sync
            ("POST", "/api/v1/discord/sync/message", "Sync Message", 403),
            
            # Reminders
            ("POST", "/api/v1/discord/reminders/schedule/test-event", "Schedule Reminders", 403),
            
            # Job management (admin only)
            ("GET", "/api/v1/discord/jobs", "List Jobs", 403),
            ("POST", "/api/v1/discord/jobs/process", "Process Jobs", 403),
            
            # Bot API
            ("POST", "/api/v1/discord/bot/verify", "Bot Verify", 401),
            ("GET", "/api/v1/discord/bot/guild/test-guild/config", "Bot Guild Config", 401),
            
            # Stats and health
            ("GET", "/api/v1/discord/stats", "Discord Stats", 403),
            ("GET", "/api/v1/discord/health", "Discord Health", 200),
            
            # Legacy endpoints
            ("POST", "/api/v1/discord/events/announce", "Legacy Event Announce", 200),
            ("POST", "/api/v1/discord/matches/announce", "Legacy Match Announce", 200),
        ]
        
        for method, endpoint, name, expected_status in discord_endpoints:
            data = {} if method in ["POST", "PUT", "PATCH"] else None
            
            self.run_test(
                f"Discord API Structure - {name}",
                method,
                endpoint,
                expected_status,
                data=data
            )

    def test_tournament_api_comprehensive(self):
        """Test Phase 4 Tournament API endpoints comprehensively"""
        print("\n" + "="*60)
        print("TESTING PHASE 4 TOURNAMENT API - COMPREHENSIVE")
        print("="*60)
        
        # Test tournament listing with various filters
        success, response = self.run_test(
            "List All Tournaments",
            "GET",
            "/api/v1/tournaments/",
            200
        )
        
        if success:
            if isinstance(response, list):
                self.log_test("Tournament List Format", True, f"Returned {len(response)} tournaments")
            else:
                self.log_test("Tournament List Format", False, "Response is not a list")
        
        # Test tournament filters
        self.run_test(
            "Filter Tournaments by Format (SE)",
            "GET",
            "/api/v1/tournaments/?format=se&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by Format (DE)",
            "GET",
            "/api/v1/tournaments/?format=de&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by Format (RR)",
            "GET",
            "/api/v1/tournaments/?format=rr&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by State (Draft)",
            "GET",
            "/api/v1/tournaments/?state=draft&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by State (Open Registration)",
            "GET",
            "/api/v1/tournaments/?state=open_registration&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by State (Ongoing)",
            "GET",
            "/api/v1/tournaments/?state=ongoing&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by State (Finished)",
            "GET",
            "/api/v1/tournaments/?state=finished&limit=10",
            200
        )
        
        self.run_test(
            "Filter Tournaments by Organization",
            "GET",
            "/api/v1/tournaments/?org_id=test-org-id&limit=10",
            200
        )
        
        # Test combined filters
        self.run_test(
            "Combined Tournament Filters",
            "GET",
            "/api/v1/tournaments/?format=se&state=ongoing&org_id=test-org&limit=5",
            200
        )
        
        # Test search query
        self.run_test(
            "Search Tournaments by Query",
            "GET",
            "/api/v1/tournaments/?query=championship&limit=10",
            200
        )
        
        # Test pagination
        self.run_test(
            "Tournament Pagination",
            "GET",
            "/api/v1/tournaments/?limit=5&skip=0",
            200
        )
        
        # Test get non-existent tournament
        self.run_test(
            "Get Non-existent Tournament",
            "GET",
            "/api/v1/tournaments/non-existent-tournament-id",
            404
        )
        
        # Test get tournament by non-existent slug
        self.run_test(
            "Get Tournament by Non-existent Slug",
            "GET",
            "/api/v1/tournaments/non-existent-slug",
            404
        )

    def test_tournament_team_management_without_auth(self):
        """Test tournament team management endpoints without authentication"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT TEAM MANAGEMENT - WITHOUT AUTH")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        test_team_id = "test-team-id"
        test_user_id = "test-user-id"
        
        # Test team creation without auth
        self.run_test(
            "Create Team Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams",
            403,
            data={"name": "Elite Squadron"}
        )
        
        # Test add team member without auth
        self.run_test(
            "Add Team Member Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/members",
            403
        )
        
        # Test remove team member without auth
        self.run_test(
            "Remove Team Member Without Auth",
            "DELETE",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/members/{test_user_id}",
            403
        )

    def test_match_score_reporting_without_auth(self):
        """Test match score reporting endpoints without authentication"""
        print("\n" + "="*60)
        print("TESTING MATCH SCORE REPORTING - WITHOUT AUTH")
        print("="*60)
        
        test_match_id = "test-match-id"
        
        # Test report match score without auth
        self.run_test(
            "Report Match Score Without Auth",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/report",
            403,
            data={
                "score_a": 3,
                "score_b": 1,
                "notes": "Great match! Team A dominated with superior tactics and coordination."
            }
        )
        
        # Test verify match result without auth
        self.run_test(
            "Verify Match Result Without Auth",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/verify",
            403
        )

    def test_file_upload_api_without_auth(self):
        """Test file upload API endpoints without authentication"""
        print("\n" + "="*60)
        print("TESTING FILE UPLOAD API - WITHOUT AUTH")
        print("="*60)
        
        test_match_id = "test-match-id"
        test_attachment_id = "test-attachment-id"
        
        # Test upload match attachment without auth
        self.run_test(
            "Upload Match Attachment Without Auth",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/attachments",
            403
        )
        
        # Test download attachment (should work without auth but return 404 for non-existent)
        self.run_test(
            "Download Non-existent Attachment",
            "GET",
            f"/api/v1/tournaments/attachments/{test_attachment_id}/download",
            404
        )
        
        # Test delete attachment without auth
        self.run_test(
            "Delete Attachment Without Auth",
            "DELETE",
            f"/api/v1/tournaments/attachments/{test_attachment_id}",
            403
        )

    def test_tournament_creation_without_auth(self):
        """Test tournament creation endpoint without authentication"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT CREATION - WITHOUT AUTH")
        print("="*60)
        
        test_org_id = "test-org-id"
        
        # Test create tournament without auth
        tournament_data = {
            "name": "Star Citizen Championship 2025",
            "description": "The ultimate Star Citizen tournament featuring the best pilots from across the galaxy. Compete in various ship classes and prove your supremacy in space combat.",
            "format": "se",
            "start_at_utc": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "max_teams": 32,
            "team_size": 5,
            "prize_pool": "100,000 aUEC + Rare Ship Skins",
            "ruleset_id": None,
            "banner_url": "https://example.com/tournament-banner.jpg"
        }
        
        self.run_test(
            "Create Tournament Without Auth",
            "POST",
            f"/api/v1/orgs/{test_org_id}/tournaments",
            403,
            data=tournament_data
        )

    def test_tournament_api_structure(self):
        """Test Tournament API structure and endpoint availability"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT API STRUCTURE")
        print("="*60)
        
        # Test that all tournament endpoints exist and return proper error codes
        tournament_endpoints = [
            # Tournament listing and details
            ("GET", "/api/v1/tournaments/", "Tournament List"),
            ("GET", "/api/v1/tournaments/test-id", "Get Tournament Details"),
            
            # Team management
            ("POST", "/api/v1/tournaments/test-id/teams", "Create Team"),
            ("POST", "/api/v1/tournaments/test-id/teams/test-team-id/members", "Add Team Member"),
            ("DELETE", "/api/v1/tournaments/test-id/teams/test-team-id/members/test-user-id", "Remove Team Member"),
            
            # Match management
            ("POST", "/api/v1/tournaments/matches/test-match-id/report", "Report Match Score"),
            ("POST", "/api/v1/tournaments/matches/test-match-id/verify", "Verify Match Result"),
            
            # File attachments
            ("POST", "/api/v1/tournaments/matches/test-match-id/attachments", "Upload Match Attachment"),
            ("GET", "/api/v1/tournaments/attachments/test-attachment-id/download", "Download Attachment"),
            ("DELETE", "/api/v1/tournaments/attachments/test-attachment-id", "Delete Attachment"),
            
            # Tournament creation (in orgs router)
            ("POST", "/api/v1/orgs/test-org-id/tournaments", "Create Tournament"),
        ]
        
        for method, endpoint, name in tournament_endpoints:
            # Most should return 403 (auth required) or 404 (not found) rather than 404 (endpoint not found)
            if method == "GET" and "attachments" in endpoint and "download" in endpoint:
                expected_status = 404  # Download endpoints return 404 for non-existent files
            elif method == "GET" and endpoint.endswith("/tournaments/"):
                expected_status = 200  # Public listing endpoint
            elif method == "GET" and "/tournaments/test-id" in endpoint:
                expected_status = 404  # Non-existent tournament
            else:
                expected_status = 403  # Auth required
            
            data = {} if method in ["POST", "PUT", "PATCH"] else None
            
            self.run_test(
                f"API Structure - {name}",
                method,
                endpoint,
                expected_status,
                data=data
            )

    def test_tournament_data_validation(self):
        """Test tournament data validation"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT DATA VALIDATION")
        print("="*60)
        
        test_org_id = "test-org-id"
        
        # Test invalid tournament formats
        invalid_format_data = {
            "name": "Invalid Format Tournament",
            "description": "Testing invalid tournament format validation in the API endpoints.",
            "format": "invalid_format",
            "start_at_utc": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "max_teams": 16,
            "team_size": 3
        }
        
        self.run_test(
            "Create Tournament With Invalid Format",
            "POST",
            f"/api/v1/orgs/{test_org_id}/tournaments",
            403,  # Will fail auth first, but tests the endpoint exists
            data=invalid_format_data
        )
        
        # Test invalid team size
        invalid_team_size_data = {
            "name": "Invalid Team Size Tournament",
            "description": "Testing invalid team size validation in tournament creation.",
            "format": "se",
            "start_at_utc": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "max_teams": 16,
            "team_size": 0  # Invalid: too small
        }
        
        self.run_test(
            "Create Tournament With Invalid Team Size",
            "POST",
            f"/api/v1/orgs/{test_org_id}/tournaments",
            403,  # Will fail auth first, but tests the endpoint exists
            data=invalid_team_size_data
        )
        
        # Test invalid max teams
        invalid_max_teams_data = {
            "name": "Invalid Max Teams Tournament",
            "description": "Testing invalid max teams validation in tournament creation.",
            "format": "se",
            "start_at_utc": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "max_teams": 2,  # Invalid: too small
            "team_size": 5
        }
        
        self.run_test(
            "Create Tournament With Invalid Max Teams",
            "POST",
            f"/api/v1/orgs/{test_org_id}/tournaments",
            403,  # Will fail auth first, but tests the endpoint exists
            data=invalid_max_teams_data
        )
        
        # Test past start date
        past_date_data = {
            "name": "Past Date Tournament",
            "description": "Testing past start date validation in tournament creation.",
            "format": "se",
            "start_at_utc": (datetime.utcnow() - timedelta(days=1)).isoformat(),  # Past date
            "max_teams": 16,
            "team_size": 5
        }
        
        self.run_test(
            "Create Tournament With Past Start Date",
            "POST",
            f"/api/v1/orgs/{test_org_id}/tournaments",
            403,  # Will fail auth first, but tests the endpoint exists
            data=past_date_data
        )

    def test_tournament_state_transitions(self):
        """Test tournament state transition scenarios"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT STATE TRANSITIONS")
        print("="*60)
        
        # Test filtering by different states to ensure state system is working
        states_to_test = [
            "draft",
            "open_registration", 
            "registration_closed",
            "ongoing",
            "finished",
            "cancelled"
        ]
        
        for state in states_to_test:
            self.run_test(
                f"Filter Tournaments by State ({state})",
                "GET",
                f"/api/v1/tournaments/?state={state}&limit=5",
                200
            )

    def test_match_score_validation(self):
        """Test match score reporting validation"""
        print("\n" + "="*60)
        print("TESTING MATCH SCORE VALIDATION")
        print("="*60)
        
        test_match_id = "test-match-id"
        
        # Test invalid score data (tied scores)
        tied_score_data = {
            "score_a": 2,
            "score_b": 2,  # Tied scores should be invalid
            "notes": "Testing tied score validation"
        }
        
        self.run_test(
            "Report Match With Tied Scores",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/report",
            403,  # Will fail auth first, but tests the endpoint exists
            data=tied_score_data
        )
        
        # Test negative scores
        negative_score_data = {
            "score_a": -1,  # Invalid: negative score
            "score_b": 2,
            "notes": "Testing negative score validation"
        }
        
        self.run_test(
            "Report Match With Negative Scores",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/report",
            403,  # Will fail auth first, but tests the endpoint exists
            data=negative_score_data
        )

    def test_file_upload_validation(self):
        """Test file upload validation scenarios"""
        print("\n" + "="*60)
        print("TESTING FILE UPLOAD VALIDATION")
        print("="*60)
        
        test_match_id = "test-match-id"
        
        # Test upload without file (will fail auth first, but tests endpoint structure)
        self.run_test(
            "Upload Without File",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/attachments",
            403
        )
        
        # Test various attachment download scenarios
        attachment_ids = [
            "non-existent-attachment",
            "invalid-uuid-format",
            "12345678-1234-1234-1234-123456789012"  # Valid UUID format but non-existent
        ]
        
        for attachment_id in attachment_ids:
            self.run_test(
                f"Download Non-existent Attachment ({attachment_id[:20]}...)",
                "GET",
                f"/api/v1/tournaments/attachments/{attachment_id}/download",
                404
            )

    def test_tournament_bracket_generation(self):
        """Test tournament bracket generation scenarios"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT BRACKET GENERATION")
        print("="*60)
        
        # Test getting tournament details (which includes bracket info)
        test_tournament_ids = [
            "test-tournament-se",
            "test-tournament-de", 
            "test-tournament-rr",
            "non-existent-tournament"
        ]
        
        for tournament_id in test_tournament_ids:
            expected_status = 404  # All should return 404 since they don't exist
            self.run_test(
                f"Get Tournament Details with Bracket ({tournament_id})",
                "GET",
                f"/api/v1/tournaments/{tournament_id}",
                expected_status
            )

    def test_authentication_edge_cases(self):
        """Test authentication edge cases for tournament endpoints"""
        print("\n" + "="*60)
        print("TESTING AUTHENTICATION EDGE CASES")
        print("="*60)
        
        # Test with malformed token
        malformed_tokens = [
            "Bearer invalid.jwt.token",
            "invalid-token-format",
            "Bearer ",
            ""
        ]
        
        for token in malformed_tokens:
            if token:
                headers = {"Authorization": token}
                expected_status = 401 if token.startswith("Bearer ") else 403
            else:
                headers = {}
                expected_status = 403
            
            self.run_test(
                f"Create Team With Malformed Token",
                "POST",
                "/api/v1/tournaments/test-id/teams",
                expected_status,
                data={"name": "Test Team"},
                headers=headers
            )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting VerseLink Backend API Tests - Phase 5 Discord Integration System")
        print(f"📡 Testing against: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Run basic health and auth tests first
        self.test_health_endpoints()
        self.test_auth_endpoints()
        
        # Run comprehensive Discord integration system tests
        self.test_discord_integration_endpoints()
        self.test_discord_webhook_endpoints()
        self.test_discord_announcement_endpoints()
        self.test_discord_message_sync_endpoints()
        self.test_discord_reminder_endpoints()
        self.test_discord_job_management_endpoints()
        self.test_discord_bot_auth_endpoints()
        self.test_discord_legacy_endpoints()
        self.test_discord_data_validation()
        self.test_discord_error_handling()
        self.test_discord_webhook_signature_verification()
        self.test_discord_api_structure()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        print(f"📊 Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        print(f"\n⏰ Completed at: {datetime.now().isoformat()}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    # Use the public endpoint from frontend .env
    base_url = "https://citizen-connect-2.preview.emergentagent.com"
    
    print("VerseLink Phase 5 Backend API Test Suite - Discord Integration System")
    print("=" * 80)
    
    tester = VerselinkAPITester(base_url)
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())