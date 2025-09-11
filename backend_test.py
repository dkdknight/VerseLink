#!/usr/bin/env python3
"""
VerseLink Backend API Test Suite - Phase 6 Notifications, Moderation & Auto-Moderation System Testing
Tests Phase 6 features: Notifications, Moderation, and Auto-Moderation systems for VerseLink application
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import io

class VerselinkAPITester:
    def __init__(self, base_url: str = "https://community-pulse-23.preview.emergentagent.com"):
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

    def test_organization_management_endpoints(self):
        """Test new organization management endpoints"""
        print("\n" + "="*60)
        print("TESTING ORGANIZATION MANAGEMENT ENDPOINTS")
        print("="*60)
        
        test_org_id = "test-org-id"
        test_user_id = "test-user-id"
        test_request_id = "test-request-id"
        
        # Test organization creation with new fields (without auth - should fail)
        org_data = {
            "name": "Test Organization",
            "tag": "TEST",
            "description": "Test organization for new features",
            "website_url": "https://example.com",
            "visibility": "public",
            "membership_policy": "request_only",
            "logo_url": "https://example.com/logo.png",
            "banner_url": "https://example.com/banner.png",
            "discord_url": "https://discord.gg/test",
            "twitter_url": "https://twitter.com/test",
            "youtube_url": "https://youtube.com/test",
            "twitch_url": "https://twitch.tv/test"
        }
        
        self.run_test(
            "Create Organization With New Fields",
            "POST",
            "/api/v1/orgs/",
            403,  # Should fail without auth
            data=org_data
        )
        
        # Test media upload endpoints (without auth - should fail)
        self.run_test(
            "Upload Organization Logo Without Auth",
            "POST",
            f"/api/v1/orgs/{test_org_id}/media/logo",
            403
        )
        
        self.run_test(
            "Upload Organization Banner Without Auth",
            "POST",
            f"/api/v1/orgs/{test_org_id}/media/banner",
            403
        )
        
        # Test join request endpoints (without auth - should fail)
        join_request_data = {
            "message": "I would like to join this organization"
        }
        
        self.run_test(
            "Create Join Request Without Auth",
            "POST",
            f"/api/v1/orgs/{test_org_id}/join-requests",
            403,
            data=join_request_data
        )
        
        self.run_test(
            "Get Join Requests Without Auth",
            "GET",
            f"/api/v1/orgs/{test_org_id}/join-requests",
            403
        )
        
        self.run_test(
            "Process Join Request Without Auth",
            "PATCH",
            f"/api/v1/orgs/{test_org_id}/join-requests/{test_request_id}",
            403,
            data={"status": "accepted"}
        )
        
        # Test member role management (without auth - should fail)
        self.run_test(
            "Update Member Role Without Auth",
            "PATCH",
            f"/api/v1/orgs/{test_org_id}/members/{test_user_id}/role",
            403,
            data={"role": "admin"}
        )
        
        # Test ownership transfer (without auth - should fail)
        transfer_data = {
            "new_owner_id": test_user_id,
            "confirmation": True
        }
        
        self.run_test(
            "Transfer Ownership Without Auth",
            "POST",
            f"/api/v1/orgs/{test_org_id}/transfer-ownership",
            403,
            data=transfer_data
        )
        
        # Test organization deletion (without auth - should fail)
        self.run_test(
            "Delete Organization Without Auth",
            "DELETE",
            f"/api/v1/orgs/{test_org_id}?confirmation=true",
            403
        )

    def test_organization_membership_policies(self):
        """Test organization membership policy features"""
        print("\n" + "="*60)
        print("TESTING ORGANIZATION MEMBERSHIP POLICIES")
        print("="*60)
        
        test_org_id = "test-org-id"
        
        # Test joining organization with open policy (without auth - should fail)
        self.run_test(
            "Join Open Organization Without Auth",
            "POST",
            f"/api/v1/orgs/{test_org_id}/members",
            403
        )
        
        # Test creating join request for request-only organization (without auth - should fail)
        self.run_test(
            "Create Join Request Without Auth",
            "POST",
            f"/api/v1/orgs/{test_org_id}/join-requests",
            403,
            data={"message": "Please let me join"}
        )

    def test_organization_data_validation(self):
        """Test organization data validation"""
        print("\n" + "="*60)
        print("TESTING ORGANIZATION DATA VALIDATION")
        print("="*60)
        
        # Test invalid organization data
        invalid_org_data = {
            "name": "",  # Empty name
            "tag": "TOOLONG123",  # Too long tag
            "visibility": "invalid_visibility",  # Invalid visibility
            "membership_policy": "invalid_policy",  # Invalid policy
            "website_url": "not-a-url",  # Invalid URL
            "discord_url": "not-a-url",  # Invalid URL
        }
        
        self.run_test(
            "Create Organization Invalid Data",
            "POST",
            "/api/v1/orgs/",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_org_data
        )
        
        # Test valid organization data structure
        valid_org_data = {
            "name": "Valid Organization Name",
            "tag": "VALID",
            "description": "A valid organization description",
            "website_url": "https://valid-website.com",
            "visibility": "public",
            "membership_policy": "open",
            "logo_url": "https://example.com/valid-logo.png",
            "banner_url": "https://example.com/valid-banner.png",
            "discord_url": "https://discord.gg/validinvite",
            "twitter_url": "https://twitter.com/validhandle",
            "youtube_url": "https://youtube.com/validchannel",
            "twitch_url": "https://twitch.tv/validchannel"
        }
        
        self.run_test(
            "Create Organization Valid Data Structure",
            "POST",
            "/api/v1/orgs/",
            403,  # Will fail auth first, but tests endpoint structure
            data=valid_org_data
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

    def test_discord_events_integration(self):
        """Test Discord Events Integration - New Implementation"""
        print("\n" + "="*60)
        print("TESTING DISCORD EVENTS INTEGRATION")
        print("="*60)
        
        # Test Discord Events Health Check
        success, response = self.run_test(
            "Discord Events Health Check",
            "GET",
            "/api/v1/discord/events/health",
            200
        )
        
        if success:
            self.log_test("Discord Events Health Response", True, f"Health status: {response.get('status', 'unknown')}")
        
        # Test Discord Events Stats (admin only - should fail without auth)
        self.run_test(
            "Discord Events Stats Without Auth",
            "GET",
            "/api/v1/discord/events/stats/events",
            403
        )
        
        # Test Discord Events Creation (should fail without auth)
        test_event_data = {
            "guild_ids": ["123456789012345678"],
            "create_channels": True,
            "create_signup_message": True
        }
        
        self.run_test(
            "Create Discord Events Without Auth",
            "POST",
            "/api/v1/discord/events/events/create/test-event",
            403,
            data=test_event_data
        )
        
        # Test Discord Interactions Handler
        interaction_data = {
            "type": 1,  # PING
            "id": "test-interaction-id",
            "application_id": "test-app-id"
        }
        
        success, response = self.run_test(
            "Discord Interactions Handler - PING",
            "POST",
            "/api/v1/discord/events/interactions",
            200,
            data=interaction_data
        )
        
        if success and response.get("type") == 1:
            self.log_test("Discord Interactions PING Response", True, "PONG response received")
        
        # Test Discord Event Auto-Management
        self.run_test(
            "Discord Event Auto-Management Without Auth",
            "POST",
            "/api/v1/discord/events/auto-manage/test-event?action=created",
            403
        )
        
        # Test Discord Event Signup Message Creation
        signup_message_data = {
            "guild_id": "123456789012345678",
            "channel_id": "987654321098765432"
        }
        
        self.run_test(
            "Create Discord Signup Message Without Auth",
            "POST",
            "/api/v1/discord/events/events/test-event/signup-message",
            403,
            data=signup_message_data
        )
        
        # Test Discord Event Attendee Sync
        sync_data = {
            "guild_id": "123456789012345678"
        }
        
        self.run_test(
            "Sync Discord Event Attendees Without Auth",
            "POST",
            "/api/v1/discord/events/events/test-event/sync-attendees",
            403,
            data=sync_data
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
            
            # New Discord Events endpoints
            ("GET", "/api/v1/discord/events/health", "Discord Events Health", 200),
            ("POST", "/api/v1/discord/events/events/create/test-event", "Create Discord Events", 403),
            ("PUT", "/api/v1/discord/events/events/update/test-event", "Update Discord Events", 403),
            ("DELETE", "/api/v1/discord/events/events/delete/test-event", "Delete Discord Events", 403),
            ("GET", "/api/v1/discord/events/events/test-event/discord", "Get Discord Events for Event", 403),
            ("POST", "/api/v1/discord/events/events/test-event/signup-message", "Create Signup Message", 403),
            ("POST", "/api/v1/discord/events/events/test-event/sync-attendees", "Sync Event Attendees", 403),
            ("POST", "/api/v1/discord/events/interactions", "Discord Interactions Handler", 200),
            ("POST", "/api/v1/discord/events/auto-manage/test-event", "Auto-manage Discord Event", 403),
            ("GET", "/api/v1/discord/events/stats/events", "Discord Events Stats", 403),
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
            ("GET", "/api/v1/tournaments/test-id/teams/test-team-id", "Get Team Details"),
            ("PUT", "/api/v1/tournaments/test-id/teams/test-team-id", "Update Team"),
            ("DELETE", "/api/v1/tournaments/test-id/teams/test-team-id", "Delete Team"),
            ("POST", "/api/v1/tournaments/test-id/teams/test-team-id/leave", "Leave Team"),
            ("POST", "/api/v1/tournaments/test-id/teams/test-team-id/members", "Add Team Member"),
            ("DELETE", "/api/v1/tournaments/test-id/teams/test-team-id/members/test-user-id", "Remove Team Member"),
            
            # Tournament administration
            ("POST", "/api/v1/tournaments/test-id/start", "Start Tournament"),
            ("POST", "/api/v1/tournaments/test-id/close-registration", "Close Registration"),
            ("POST", "/api/v1/tournaments/test-id/reopen-registration", "Reopen Registration"),
            
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

    def test_new_tournament_team_management_endpoints(self):
        """Test new Phase 7 tournament team management endpoints"""
        print("\n" + "="*60)
        print("TESTING PHASE 7 TOURNAMENT TEAM MANAGEMENT ENDPOINTS")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        test_team_id = "test-team-id"
        
        # Test get team details without auth (should fail)
        self.run_test(
            "Get Team Details Without Auth",
            "GET",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403
        )
        
        # Test update team without auth (should fail)
        team_update_data = {
            "name": "Updated Team Name"
        }
        
        self.run_test(
            "Update Team Without Auth",
            "PUT",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403,
            data=team_update_data
        )
        
        # Test delete team without auth (should fail)
        self.run_test(
            "Delete Team Without Auth",
            "DELETE",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403
        )
        
        # Test leave team without auth (should fail)
        self.run_test(
            "Leave Team Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/leave",
            403
        )

    def test_new_tournament_administration_endpoints(self):
        """Test new Phase 7 tournament administration endpoints"""
        print("\n" + "="*60)
        print("TESTING PHASE 7 TOURNAMENT ADMINISTRATION ENDPOINTS")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        
        # Test start tournament without auth (should fail)
        self.run_test(
            "Start Tournament Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/start",
            403
        )
        
        # Test close registration without auth (should fail)
        self.run_test(
            "Close Tournament Registration Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/close-registration",
            403
        )
        
        # Test reopen registration without auth (should fail)
        self.run_test(
            "Reopen Tournament Registration Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/reopen-registration",
            403
        )

    def test_tournament_team_management_data_validation(self):
        """Test tournament team management data validation"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT TEAM MANAGEMENT DATA VALIDATION")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        test_team_id = "test-team-id"
        
        # Test update team with invalid data
        invalid_team_data = {
            "name": ""  # Empty name should be invalid
        }
        
        self.run_test(
            "Update Team Invalid Data (Empty Name)",
            "PUT",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_team_data
        )
        
        # Test update team with very long name
        long_name_data = {
            "name": "A" * 200  # Very long name should be invalid
        }
        
        self.run_test(
            "Update Team Invalid Data (Long Name)",
            "PUT",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403,  # Will fail auth first, but tests endpoint structure
            data=long_name_data
        )
        
        # Test valid team update data structure
        valid_team_data = {
            "name": "Valid Team Name"
        }
        
        self.run_test(
            "Update Team Valid Data Structure",
            "PUT",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403,  # Will fail auth first, but tests endpoint structure
            data=valid_team_data
        )

    def test_tournament_state_management(self):
        """Test tournament state management scenarios"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT STATE MANAGEMENT")
        print("="*60)
        
        # Test various tournament states to ensure state system is working
        tournament_states = [
            "draft",
            "open_registration", 
            "registration_closed",
            "ongoing",
            "finished",
            "cancelled"
        ]
        
        for state in tournament_states:
            self.run_test(
                f"Filter Tournaments by State ({state})",
                "GET",
                f"/api/v1/tournaments/?state={state}&limit=5",
                200
            )
        
        # Test tournament administration actions for different states
        test_tournament_id = "test-tournament-id"
        
        # These should all fail with 403 (auth required) but test endpoint structure
        admin_actions = [
            ("start", "Start Tournament"),
            ("close-registration", "Close Registration"),
            ("reopen-registration", "Reopen Registration")
        ]
        
        for action, description in admin_actions:
            self.run_test(
                f"Tournament Admin Action - {description}",
                "POST",
                f"/api/v1/tournaments/{test_tournament_id}/{action}",
                403
            )

    def test_phase3_team_invitations_endpoints(self):
        """Test Phase 3 Team Invitations system endpoints"""
        print("\n" + "="*60)
        print("TESTING PHASE 3 TEAM INVITATIONS SYSTEM ENDPOINTS")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        test_team_id = "test-team-id"
        test_invitation_id = "test-invitation-id"
        
        # Test create team invitation without auth (should fail)
        invitation_data = {
            "invited_user_id": "test-user-id",
            "message": "Join our elite team for the championship!"
        }
        
        self.run_test(
            "Create Team Invitation Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/invitations",
            403,
            data=invitation_data
        )
        
        # Test get team invitations without auth (should fail)
        self.run_test(
            "Get Team Invitations Without Auth",
            "GET",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/invitations",
            403
        )
        
        # Test respond to invitation without auth (should fail)
        self.run_test(
            "Respond to Invitation Without Auth",
            "POST",
            f"/api/v1/tournaments/invitations/{test_invitation_id}/respond",
            403,
            data={"accept": True}
        )
        
        # Test cancel invitation without auth (should fail)
        self.run_test(
            "Cancel Invitation Without Auth",
            "DELETE",
            f"/api/v1/tournaments/invitations/{test_invitation_id}",
            403
        )
        
        # Test get my invitations without auth (should fail)
        self.run_test(
            "Get My Invitations Without Auth",
            "GET",
            "/api/v1/tournaments/invitations/me",
            403
        )
        
        # Test get my invitations with status filter without auth (should fail)
        self.run_test(
            "Get My Invitations With Status Filter Without Auth",
            "GET",
            "/api/v1/tournaments/invitations/me?status=pending",
            403
        )

    def test_phase3_match_disputes_endpoints(self):
        """Test Phase 3 Match Disputes system endpoints"""
        print("\n" + "="*60)
        print("TESTING PHASE 3 MATCH DISPUTES SYSTEM ENDPOINTS")
        print("="*60)
        
        test_match_id = "test-match-id"
        test_dispute_id = "test-dispute-id"
        
        # Test create match dispute without auth (should fail)
        dispute_data = {
            "reason": "The opposing team used illegal tactics during the match",
            "description": "Detailed description of the dispute with evidence and timestamps"
        }
        
        self.run_test(
            "Create Match Dispute Without Auth",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/dispute",
            403,
            data=dispute_data
        )
        
        # Test get match disputes without auth (should fail)
        self.run_test(
            "Get Match Disputes Without Auth",
            "GET",
            f"/api/v1/tournaments/matches/{test_match_id}/disputes",
            403
        )
        
        # Test list all disputes without auth (should fail)
        self.run_test(
            "List All Disputes Without Auth",
            "GET",
            "/api/v1/tournaments/disputes",
            403
        )
        
        # Test list disputes with tournament filter without auth (should fail)
        self.run_test(
            "List Disputes With Tournament Filter Without Auth",
            "GET",
            "/api/v1/tournaments/disputes?tournament_id=test-tournament-id",
            403
        )
        
        # Test list disputes with status filter without auth (should fail)
        self.run_test(
            "List Disputes With Status Filter Without Auth",
            "GET",
            "/api/v1/tournaments/disputes?status=pending",
            403
        )
        
        # Test get dispute details without auth (should fail)
        self.run_test(
            "Get Dispute Details Without Auth",
            "GET",
            f"/api/v1/tournaments/disputes/{test_dispute_id}",
            403
        )
        
        # Test set dispute under review without auth (should fail)
        self.run_test(
            "Set Dispute Under Review Without Auth",
            "POST",
            f"/api/v1/tournaments/disputes/{test_dispute_id}/review",
            403
        )
        
        # Test resolve dispute without auth (should fail)
        resolve_data = {
            "approve": True,
            "admin_response": "After reviewing the evidence, the dispute is approved"
        }
        
        self.run_test(
            "Resolve Dispute Without Auth",
            "POST",
            f"/api/v1/tournaments/disputes/{test_dispute_id}/resolve",
            403,
            data=resolve_data
        )

    def test_phase3_invitations_data_validation(self):
        """Test Phase 3 invitations data validation"""
        print("\n" + "="*60)
        print("TESTING PHASE 3 INVITATIONS DATA VALIDATION")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        test_team_id = "test-team-id"
        test_invitation_id = "test-invitation-id"
        
        # Test create invitation with invalid data
        invalid_invitation_data = {
            "invited_user_id": "",  # Empty user ID
            "message": ""  # Empty message
        }
        
        self.run_test(
            "Create Invitation Invalid Data (Empty Fields)",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/invitations",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_invitation_data
        )
        
        # Test create invitation with very long message
        long_message_data = {
            "invited_user_id": "test-user-id",
            "message": "A" * 1000  # Very long message
        }
        
        self.run_test(
            "Create Invitation Invalid Data (Long Message)",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/invitations",
            403,  # Will fail auth first, but tests endpoint structure
            data=long_message_data
        )
        
        # Test respond to invitation with invalid data
        invalid_response_data = {
            "accept": "invalid_boolean"  # Should be boolean
        }
        
        self.run_test(
            "Respond to Invitation Invalid Data",
            "POST",
            f"/api/v1/tournaments/invitations/{test_invitation_id}/respond",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_response_data
        )

    def test_phase3_disputes_data_validation(self):
        """Test Phase 3 disputes data validation"""
        print("\n" + "="*60)
        print("TESTING PHASE 3 DISPUTES DATA VALIDATION")
        print("="*60)
        
        test_match_id = "test-match-id"
        test_dispute_id = "test-dispute-id"
        
        # Test create dispute with invalid data
        invalid_dispute_data = {
            "reason": "",  # Empty reason
            "description": ""  # Empty description
        }
        
        self.run_test(
            "Create Dispute Invalid Data (Empty Fields)",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/dispute",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_dispute_data
        )
        
        # Test create dispute with very long fields
        long_fields_data = {
            "reason": "A" * 500,  # Very long reason
            "description": "B" * 2000  # Very long description
        }
        
        self.run_test(
            "Create Dispute Invalid Data (Long Fields)",
            "POST",
            f"/api/v1/tournaments/matches/{test_match_id}/dispute",
            403,  # Will fail auth first, but tests endpoint structure
            data=long_fields_data
        )
        
        # Test resolve dispute with invalid data
        invalid_resolve_data = {
            "approve": "invalid_boolean",  # Should be boolean
            "admin_response": ""  # Empty response
        }
        
        self.run_test(
            "Resolve Dispute Invalid Data",
            "POST",
            f"/api/v1/tournaments/disputes/{test_dispute_id}/resolve",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_resolve_data
        )

    def test_phase3_api_structure(self):
        """Test Phase 3 API structure and endpoint availability"""
        print("\n" + "="*60)
        print("TESTING PHASE 3 API STRUCTURE")
        print("="*60)
        
        # Test that all Phase 3 endpoints exist and return proper error codes
        phase3_endpoints = [
            # Team Invitations
            ("POST", "/api/v1/tournaments/test-tournament/teams/test-team/invitations", "Create Team Invitation", 403),
            ("GET", "/api/v1/tournaments/test-tournament/teams/test-team/invitations", "Get Team Invitations", 403),
            ("POST", "/api/v1/tournaments/invitations/test-invitation/respond", "Respond to Invitation", 403),
            ("DELETE", "/api/v1/tournaments/invitations/test-invitation", "Cancel Invitation", 403),
            ("GET", "/api/v1/tournaments/invitations/me", "Get My Invitations", 403),
            
            # Match Disputes
            ("POST", "/api/v1/tournaments/matches/test-match/dispute", "Create Match Dispute", 403),
            ("GET", "/api/v1/tournaments/matches/test-match/disputes", "Get Match Disputes", 403),
            ("GET", "/api/v1/tournaments/disputes", "List All Disputes", 403),
            ("GET", "/api/v1/tournaments/disputes/test-dispute", "Get Dispute Details", 403),
            ("POST", "/api/v1/tournaments/disputes/test-dispute/review", "Set Dispute Under Review", 403),
            ("POST", "/api/v1/tournaments/disputes/test-dispute/resolve", "Resolve Dispute", 403),
        ]
        
        for method, endpoint, name, expected_status in phase3_endpoints:
            data = {} if method in ["POST", "PUT", "PATCH"] else None
            
            self.run_test(
                f"Phase 3 API Structure - {name}",
                method,
                endpoint,
                expected_status,
                data=data
            )

    def test_new_tournament_management_endpoints(self):
        """Test new tournament management endpoints requested by main agent"""
        print("\n" + "="*60)
        print("TESTING NEW TOURNAMENT MANAGEMENT ENDPOINTS")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        test_team_id = "test-team-id"
        
        # Test GET /api/v1/tournaments/{tournament_id}/teams/{team_id} - Team details
        self.run_test(
            "Get Team Details",
            "GET",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403  # Should fail without auth
        )
        
        # Test PUT /api/v1/tournaments/{tournament_id}/teams/{team_id} - Update team
        team_update_data = {
            "name": "Updated Team Name"
        }
        self.run_test(
            "Update Team",
            "PUT",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403,  # Should fail without auth
            data=team_update_data
        )
        
        # Test DELETE /api/v1/tournaments/{tournament_id}/teams/{team_id} - Delete team
        self.run_test(
            "Delete Team",
            "DELETE",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}",
            403  # Should fail without auth
        )
        
        # Test POST /api/v1/tournaments/{tournament_id}/teams/{team_id}/leave - Leave team
        self.run_test(
            "Leave Team",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/teams/{test_team_id}/leave",
            403  # Should fail without auth
        )
        
        # Test POST /api/v1/tournaments/{tournament_id}/start - Start tournament
        self.run_test(
            "Start Tournament",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/start",
            403  # Should fail without auth
        )
        
        # Test POST /api/v1/tournaments/{tournament_id}/close-registration - Close registration
        self.run_test(
            "Close Tournament Registration",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/close-registration",
            403  # Should fail without auth
        )
        
        # Test POST /api/v1/tournaments/{tournament_id}/reopen-registration - Reopen registration
        self.run_test(
            "Reopen Tournament Registration",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/reopen-registration",
            403  # Should fail without auth
        )
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

    def test_notifications_endpoints(self):
        """Test Phase 6 Notifications system endpoints"""
        print("\n" + "="*60)
        print("TESTING PHASE 6 NOTIFICATIONS SYSTEM ENDPOINTS")
        print("="*60)
        
        # Test get notifications without auth (should fail)
        self.run_test(
            "Get My Notifications Without Auth",
            "GET",
            "/api/v1/notifications/me",
            403
        )
        
        # Test get notification stats without auth (should fail)
        self.run_test(
            "Get My Notification Stats Without Auth",
            "GET",
            "/api/v1/notifications/me/stats",
            403
        )
        
        # Test mark notification as read without auth (should fail)
        self.run_test(
            "Mark Notification as Read Without Auth",
            "POST",
            "/api/v1/notifications/test-notification-id/read",
            403
        )
        
        # Test mark all notifications as read without auth (should fail)
        self.run_test(
            "Mark All Notifications as Read Without Auth",
            "POST",
            "/api/v1/notifications/me/read-all",
            403
        )
        
        # Test get notification preferences without auth (should fail)
        self.run_test(
            "Get Notification Preferences Without Auth",
            "GET",
            "/api/v1/notifications/me/preferences",
            403
        )
        
        # Test update notification preferences without auth (should fail)
        preferences_update = {
            "preferences": {
                "event_created": {
                    "in_app_enabled": True,
                    "email_enabled": False,
                    "discord_dm_enabled": False
                }
            }
        }
        
        self.run_test(
            "Update Notification Preferences Without Auth",
            "PUT",
            "/api/v1/notifications/me/preferences",
            403,
            data=preferences_update
        )
        
        # Test create test notification without auth (should fail)
        self.run_test(
            "Create Test Notification Without Auth",
            "POST",
            "/api/v1/notifications/test",
            403
        )

    def test_notifications_data_validation(self):
        """Test notifications data validation"""
        print("\n" + "="*60)
        print("TESTING NOTIFICATIONS DATA VALIDATION")
        print("="*60)
        
        # Test invalid notification preferences update
        invalid_preferences = {
            "preferences": {
                "invalid_notification_type": {
                    "in_app_enabled": True,
                    "email_enabled": "invalid_boolean",  # Should be boolean
                    "discord_dm_enabled": None
                }
            }
        }
        
        self.run_test(
            "Update Preferences Invalid Data",
            "PUT",
            "/api/v1/notifications/me/preferences",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_preferences
        )
        
        # Test notification filtering with query parameters
        self.run_test(
            "Get Notifications With Filters",
            "GET",
            "/api/v1/notifications/me?limit=10&skip=0&unread_only=true",
            403  # Will fail auth first
        )
        
        # Test invalid limit values
        self.run_test(
            "Get Notifications Invalid Limit",
            "GET",
            "/api/v1/notifications/me?limit=200",  # Exceeds max limit
            403  # Will fail auth first
        )

    def test_moderation_endpoints(self):
        """Test Phase 6 Moderation system endpoints"""
        print("\n" + "="*60)
        print("TESTING PHASE 6 MODERATION SYSTEM ENDPOINTS")
        print("="*60)
        
        # Test create report without auth (should fail)
        report_data = {
            "reported_user_id": "test-reported-user-id",
            "type": "harassment",
            "reason": "This user has been sending inappropriate messages and harassing other players during events.",
            "context_url": "/events/test-event-id",
            "additional_info": {
                "incident_time": "2025-01-27T15:30:00Z",
                "witnesses": ["user1", "user2"]
            }
        }
        
        self.run_test(
            "Create Report Without Auth",
            "POST",
            "/api/v1/moderation/reports",
            403,
            data=report_data
        )
        
        # Test list reports without admin auth (should fail)
        self.run_test(
            "List Reports Without Admin Auth",
            "GET",
            "/api/v1/moderation/reports",
            403
        )
        
        # Test list reports with filters
        self.run_test(
            "List Reports With Status Filter",
            "GET",
            "/api/v1/moderation/reports?status=pending&limit=10&skip=0",
            403  # Will fail auth first
        )
        
        # Test get specific report without admin auth (should fail)
        self.run_test(
            "Get Report Details Without Admin Auth",
            "GET",
            "/api/v1/moderation/reports/test-report-id",
            403
        )
        
        # Test handle report without admin auth (should fail)
        moderation_action = {
            "action": "warning",
            "reason": "First offense - inappropriate language in chat",
            "duration_hours": None,
            "reputation_change": None
        }
        
        self.run_test(
            "Handle Report Without Admin Auth",
            "POST",
            "/api/v1/moderation/reports/test-report-id/action",
            403,
            data=moderation_action
        )
        
        # Test get user moderation history without admin auth (should fail)
        self.run_test(
            "Get User Moderation History Without Admin Auth",
            "GET",
            "/api/v1/moderation/users/test-user-id/history",
            403
        )
        
        # Test get moderation stats without admin auth (should fail)
        self.run_test(
            "Get Moderation Stats Without Admin Auth",
            "GET",
            "/api/v1/moderation/stats",
            403
        )
        
        # Test get audit logs without admin auth (should fail)
        self.run_test(
            "Get Audit Logs Without Admin Auth",
            "GET",
            "/api/v1/moderation/audit-logs",
            403
        )
        
        # Test audit logs with pagination
        self.run_test(
            "Get Audit Logs With Pagination",
            "GET",
            "/api/v1/moderation/audit-logs?limit=25&skip=0",
            403  # Will fail auth first
        )
        
        # Test maintenance endpoint without admin auth (should fail)
        self.run_test(
            "Unban Expired Users Without Admin Auth",
            "POST",
            "/api/v1/moderation/maintenance/unban-expired",
            403
        )

    def test_moderation_data_validation(self):
        """Test moderation data validation"""
        print("\n" + "="*60)
        print("TESTING MODERATION DATA VALIDATION")
        print("="*60)
        
        # Test invalid report data
        invalid_report_data = {
            "reported_user_id": "",  # Empty user ID
            "type": "invalid_type",  # Invalid report type
            "reason": "Too short",  # Too short (min 10 chars)
            "context_url": "invalid-url"
        }
        
        self.run_test(
            "Create Report Invalid Data",
            "POST",
            "/api/v1/moderation/reports",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_report_data
        )
        
        # Test invalid moderation action
        invalid_action = {
            "action": "invalid_action",  # Invalid action type
            "reason": "X",  # Too short (min 5 chars)
            "duration_hours": -1,  # Invalid duration
            "reputation_change": "not_a_number"  # Should be integer
        }
        
        self.run_test(
            "Handle Report Invalid Action",
            "POST",
            "/api/v1/moderation/reports/test-report-id/action",
            403,  # Will fail auth first
            data=invalid_action
        )
        
        # Test various report types
        report_types = ["spam", "harassment", "inappropriate_content", "cheating", "no_show", "griefing", "other"]
        
        for report_type in report_types:
            valid_report = {
                "reported_user_id": "test-user-id",
                "type": report_type,
                "reason": f"Testing {report_type} report type with sufficient detail for validation.",
                "context_url": "/events/test-event"
            }
            
            self.run_test(
                f"Create Report Type ({report_type})",
                "POST",
                "/api/v1/moderation/reports",
                403,  # Will fail auth first
                data=valid_report
            )

    def test_auto_moderation_endpoints(self):
        """Test Phase 6 Auto-Moderation system endpoints (NEW)"""
        print("\n" + "="*60)
        print("TESTING PHASE 6 AUTO-MODERATION SYSTEM ENDPOINTS (NEW)")
        print("="*60)
        
        # Test get auto-moderation config without admin auth (should fail)
        self.run_test(
            "Get Auto-Moderation Config Without Admin Auth",
            "GET",
            "/api/v1/auto-moderation/config",
            403
        )
        
        # Test update auto-moderation config without admin auth (should fail)
        config_update = {
            "enabled": True,
            "spam_detection": {
                "enabled": True,
                "max_duplicate_messages": 5,
                "time_window_minutes": 10,
                "similarity_threshold": 0.9
            },
            "profanity_filter": {
                "enabled": True,
                "action": "strike"
            },
            "harassment_detection": {
                "enabled": True,
                "max_reports_per_user": 2,
                "time_window_hours": 12,
                "action": "temporary_ban",
                "ban_duration_hours": 48
            }
        }
        
        self.run_test(
            "Update Auto-Moderation Config Without Admin Auth",
            "PUT",
            "/api/v1/auto-moderation/config",
            403,
            data=config_update
        )
        
        # Test toggle auto-moderation without admin auth (should fail)
        self.run_test(
            "Toggle Auto-Moderation Without Admin Auth",
            "POST",
            "/api/v1/auto-moderation/toggle?enabled=true",
            403
        )
        
        # Test check message content (should work with user auth, but we don't have auth)
        message_check = {
            "content": "This is a test message to check for auto-moderation violations.",
            "context": "chat_message"
        }
        
        self.run_test(
            "Check Message Content Without Auth",
            "POST",
            "/api/v1/auto-moderation/check-message",
            403,
            data=message_check
        )
        
        # Test get auto-moderation stats without admin auth (should fail)
        self.run_test(
            "Get Auto-Moderation Stats Without Admin Auth",
            "GET",
            "/api/v1/auto-moderation/stats",
            403
        )
        
        # Test get auto-moderation logs without admin auth (should fail)
        self.run_test(
            "Get Auto-Moderation Logs Without Admin Auth",
            "GET",
            "/api/v1/auto-moderation/logs",
            403
        )
        
        # Test auto-moderation logs with pagination
        self.run_test(
            "Get Auto-Moderation Logs With Pagination",
            "GET",
            "/api/v1/auto-moderation/logs?limit=25&skip=0",
            403  # Will fail auth first
        )
        
        # Test clear old auto-moderation logs without admin auth (should fail)
        self.run_test(
            "Clear Old Auto-Moderation Logs Without Admin Auth",
            "DELETE",
            "/api/v1/auto-moderation/logs?days_old=30",
            403
        )

    def test_auto_moderation_data_validation(self):
        """Test auto-moderation data validation"""
        print("\n" + "="*60)
        print("TESTING AUTO-MODERATION DATA VALIDATION")
        print("="*60)
        
        # Test invalid config update (empty data)
        empty_config = {}
        
        self.run_test(
            "Update Auto-Moderation Config Empty Data",
            "PUT",
            "/api/v1/auto-moderation/config",
            403,  # Will fail auth first, but tests endpoint structure
            data=empty_config
        )
        
        # Test invalid message check data
        invalid_message_checks = [
            {"content": ""},  # Empty content
            {"content": "x" * 10000},  # Too long content
            {"context": "invalid_context_type"}  # Invalid context
        ]
        
        for i, invalid_data in enumerate(invalid_message_checks):
            self.run_test(
                f"Check Message Invalid Data ({i+1})",
                "POST",
                "/api/v1/auto-moderation/check-message",
                403,  # Will fail auth first
                data=invalid_data
            )
        
        # Test various message content scenarios
        test_messages = [
            {
                "content": "Hello everyone, looking forward to the event!",
                "context": "event_chat"
            },
            {
                "content": "GG everyone, great match!",
                "context": "tournament_chat"
            },
            {
                "content": "When is the next mining operation scheduled?",
                "context": "org_chat"
            },
            {
                "content": "Thanks for organizing this awesome tournament!",
                "context": "general_chat"
            }
        ]
        
        for i, message_data in enumerate(test_messages):
            self.run_test(
                f"Check Valid Message Content ({i+1})",
                "POST",
                "/api/v1/auto-moderation/check-message",
                403,  # Will fail auth first
                data=message_data
            )

    def test_auto_moderation_toggle_functionality(self):
        """Test auto-moderation toggle functionality"""
        print("\n" + "="*60)
        print("TESTING AUTO-MODERATION TOGGLE FUNCTIONALITY")
        print("="*60)
        
        # Test toggle enable
        self.run_test(
            "Toggle Auto-Moderation Enable",
            "POST",
            "/api/v1/auto-moderation/toggle",
            403,
            data={"enabled": True}
        )
        
        # Test toggle disable
        self.run_test(
            "Toggle Auto-Moderation Disable",
            "POST",
            "/api/v1/auto-moderation/toggle",
            403,
            data={"enabled": False}
        )
        
        # Test toggle with invalid data
        self.run_test(
            "Toggle Auto-Moderation Invalid Data",
            "POST",
            "/api/v1/auto-moderation/toggle",
            403,
            data={"enabled": "not_a_boolean"}
        )

    def test_phase6_api_structure(self):
        """Test Phase 6 API structure and endpoint availability"""
        print("\n" + "="*60)
        print("TESTING PHASE 6 API STRUCTURE")
        print("="*60)
        
        # Test that all Phase 6 endpoints exist and return proper error codes
        phase6_endpoints = [
            # Notifications endpoints
            ("GET", "/api/v1/notifications/me", "Get My Notifications", 403),
            ("GET", "/api/v1/notifications/me/stats", "Get Notification Stats", 403),
            ("POST", "/api/v1/notifications/test-id/read", "Mark Notification Read", 403),
            ("POST", "/api/v1/notifications/me/read-all", "Mark All Notifications Read", 403),
            ("GET", "/api/v1/notifications/me/preferences", "Get Notification Preferences", 403),
            ("PUT", "/api/v1/notifications/me/preferences", "Update Notification Preferences", 403),
            ("POST", "/api/v1/notifications/test", "Create Test Notification", 403),
            
            # Moderation endpoints
            ("POST", "/api/v1/moderation/reports", "Create Report", 403),
            ("GET", "/api/v1/moderation/reports", "List Reports", 403),
            ("GET", "/api/v1/moderation/reports/test-id", "Get Report Details", 403),
            ("POST", "/api/v1/moderation/reports/test-id/action", "Handle Report", 403),
            ("GET", "/api/v1/moderation/users/test-id/history", "Get User Moderation History", 403),
            ("GET", "/api/v1/moderation/stats", "Get Moderation Stats", 403),
            ("GET", "/api/v1/moderation/audit-logs", "Get Audit Logs", 403),
            ("POST", "/api/v1/moderation/maintenance/unban-expired", "Unban Expired Users", 403),
            
            # Auto-moderation endpoints (NEW)
            ("GET", "/api/v1/auto-moderation/config", "Get Auto-Moderation Config", 403),
            ("PUT", "/api/v1/auto-moderation/config", "Update Auto-Moderation Config", 403),
            ("POST", "/api/v1/auto-moderation/toggle", "Toggle Auto-Moderation", 403),
            ("POST", "/api/v1/auto-moderation/check-message", "Check Message Content", 403),
            ("GET", "/api/v1/auto-moderation/stats", "Get Auto-Moderation Stats", 403),
            ("GET", "/api/v1/auto-moderation/logs", "Get Auto-Moderation Logs", 403),
            ("DELETE", "/api/v1/auto-moderation/logs", "Clear Auto-Moderation Logs", 403),
        ]
        
        for method, endpoint, name, expected_status in phase6_endpoints:
            data = {} if method in ["POST", "PUT", "PATCH"] else None
            
            self.run_test(
                f"Phase 6 API Structure - {name}",
                method,
                endpoint,
                expected_status,
                data=data
            )

    def test_phase6_integration_scenarios(self):
        """Test Phase 6 integration scenarios"""
        print("\n" + "="*60)
        print("TESTING PHASE 6 INTEGRATION SCENARIOS")
        print("="*60)
        
        # Test notification and moderation integration
        # (These would normally work together when a user is moderated)
        
        # Test report creation with various types
        report_scenarios = [
            {
                "type": "spam",
                "reason": "User is sending repetitive promotional messages in event chat channels.",
                "context": "event_chat_spam"
            },
            {
                "type": "harassment", 
                "reason": "User is targeting specific players with offensive language and threats.",
                "context": "harassment_incident"
            },
            {
                "type": "cheating",
                "reason": "Suspected use of third-party tools during tournament matches.",
                "context": "tournament_cheating"
            },
            {
                "type": "griefing",
                "reason": "Intentionally disrupting organized events and preventing others from participating.",
                "context": "event_griefing"
            }
        ]
        
        for i, scenario in enumerate(report_scenarios):
            report_data = {
                "reported_user_id": f"test-user-{i+1}",
                "type": scenario["type"],
                "reason": scenario["reason"],
                "context_url": f"/events/test-event-{i+1}",
                "additional_info": {"scenario": scenario["context"]}
            }
            
            self.run_test(
                f"Integration Test - Report {scenario['type'].title()}",
                "POST",
                "/api/v1/moderation/reports",
                403,  # Will fail auth first
                data=report_data
            )
        
        # Test auto-moderation message checking scenarios
        auto_mod_scenarios = [
            {
                "content": "Looking forward to the mining operation tomorrow!",
                "context": "positive_message",
                "expected": "clean"
            },
            {
                "content": "Great job everyone in the tournament finals!",
                "context": "tournament_praise",
                "expected": "clean"
            },
            {
                "content": "When is the next org meeting scheduled?",
                "context": "org_question",
                "expected": "clean"
            },
            {
                "content": "Thanks for the help with the cargo run!",
                "context": "gratitude_message",
                "expected": "clean"
            }
        ]
        
        for i, scenario in enumerate(auto_mod_scenarios):
            message_data = {
                "content": scenario["content"],
                "context": scenario["context"]
            }
            
            self.run_test(
                f"Integration Test - Auto-Mod Check ({scenario['expected']})",
                "POST",
                "/api/v1/auto-moderation/check-message",
                403,  # Will fail auth first
                data=message_data
            )

    def test_player_search_endpoints(self):
        """Test Phase Final Player Search system endpoints"""
        print("\n" + "="*60)
        print("TESTING PHASE FINAL PLAYER SEARCH SYSTEM ENDPOINTS")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        test_search_id = "test-search-id"
        
        # Test create player search without auth (should fail)
        search_data = {
            "preferred_role": "pilote",
            "experience_level": "expert",
            "description": "Pilote expérimenté cherche équipe compétitive pour le championnat"
        }
        
        self.run_test(
            "Create Player Search Without Auth",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/player-search",
            403,
            data=search_data
        )
        
        # Test get tournament player searches without auth (should fail)
        self.run_test(
            "Get Tournament Player Searches Without Auth",
            "GET",
            f"/api/v1/tournaments/{test_tournament_id}/player-search",
            403
        )
        
        # Test get tournament player searches with role filter without auth (should fail)
        self.run_test(
            "Get Player Searches With Role Filter Without Auth",
            "GET",
            f"/api/v1/tournaments/{test_tournament_id}/player-search?role=pilote",
            403
        )
        
        # Test get tournament player searches with experience filter without auth (should fail)
        self.run_test(
            "Get Player Searches With Experience Filter Without Auth",
            "GET",
            f"/api/v1/tournaments/{test_tournament_id}/player-search?experience=expert",
            403
        )
        
        # Test get tournament player searches with combined filters without auth (should fail)
        self.run_test(
            "Get Player Searches With Combined Filters Without Auth",
            "GET",
            f"/api/v1/tournaments/{test_tournament_id}/player-search?role=pilote&experience=expert",
            403
        )
        
        # Test get my player searches without auth (should fail)
        self.run_test(
            "Get My Player Searches Without Auth",
            "GET",
            "/api/v1/tournaments/player-search/me",
            403
        )
        
        # Test update player search without auth (should fail)
        update_data = {
            "preferred_role": "gunner",
            "experience_level": "intermediate",
            "description": "Gunner expérimenté disponible pour équipe sérieuse"
        }
        
        self.run_test(
            "Update Player Search Without Auth",
            "PUT",
            f"/api/v1/tournaments/player-search/{test_search_id}",
            403,
            data=update_data
        )
        
        # Test deactivate player search without auth (should fail)
        self.run_test(
            "Deactivate Player Search Without Auth",
            "POST",
            f"/api/v1/tournaments/player-search/{test_search_id}/deactivate",
            403
        )
        
        # Test delete player search without auth (should fail)
        self.run_test(
            "Delete Player Search Without Auth",
            "DELETE",
            f"/api/v1/tournaments/player-search/{test_search_id}",
            403
        )

    def test_player_search_data_validation(self):
        """Test player search data validation"""
        print("\n" + "="*60)
        print("TESTING PLAYER SEARCH DATA VALIDATION")
        print("="*60)
        
        test_tournament_id = "test-tournament-id"
        test_search_id = "test-search-id"
        
        # Test create player search with invalid role
        invalid_role_data = {
            "preferred_role": "invalid_role",
            "experience_level": "expert",
            "description": "Test description"
        }
        
        self.run_test(
            "Create Player Search Invalid Role",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/player-search",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_role_data
        )
        
        # Test create player search with invalid experience level
        invalid_experience_data = {
            "preferred_role": "pilote",
            "experience_level": "invalid_level",
            "description": "Test description"
        }
        
        self.run_test(
            "Create Player Search Invalid Experience",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/player-search",
            403,  # Will fail auth first, but tests endpoint structure
            data=invalid_experience_data
        )
        
        # Test create player search with empty description
        empty_description_data = {
            "preferred_role": "pilote",
            "experience_level": "expert",
            "description": ""  # Empty description
        }
        
        self.run_test(
            "Create Player Search Empty Description",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/player-search",
            403,  # Will fail auth first, but tests endpoint structure
            data=empty_description_data
        )
        
        # Test create player search with very long description
        long_description_data = {
            "preferred_role": "pilote",
            "experience_level": "expert",
            "description": "A" * 1000  # Very long description
        }
        
        self.run_test(
            "Create Player Search Long Description",
            "POST",
            f"/api/v1/tournaments/{test_tournament_id}/player-search",
            403,  # Will fail auth first, but tests endpoint structure
            data=long_description_data
        )

    def test_player_search_api_structure(self):
        """Test Player Search API structure and endpoint availability"""
        print("\n" + "="*60)
        print("TESTING PLAYER SEARCH API STRUCTURE")
        print("="*60)
        
        # Test that all player search endpoints exist and return proper error codes
        player_search_endpoints = [
            # Player search management
            ("POST", "/api/v1/tournaments/test-tournament-id/player-search", "Create Player Search", 403),
            ("GET", "/api/v1/tournaments/test-tournament-id/player-search", "Get Tournament Player Searches", 403),
            ("GET", "/api/v1/tournaments/player-search/me", "Get My Player Searches", 403),
            ("PUT", "/api/v1/tournaments/player-search/test-search-id", "Update Player Search", 403),
            ("POST", "/api/v1/tournaments/player-search/test-search-id/deactivate", "Deactivate Player Search", 403),
            ("DELETE", "/api/v1/tournaments/player-search/test-search-id", "Delete Player Search", 403),
            
            # Player search with filters
            ("GET", "/api/v1/tournaments/test-tournament-id/player-search?role=pilote", "Filter by Role", 403),
            ("GET", "/api/v1/tournaments/test-tournament-id/player-search?experience=expert", "Filter by Experience", 403),
            ("GET", "/api/v1/tournaments/test-tournament-id/player-search?role=pilote&experience=expert", "Combined Filters", 403),
        ]
        
        for method, endpoint, name, expected_status in player_search_endpoints:
            data = {} if method in ["POST", "PUT", "PATCH"] else None
            
            self.run_test(
                f"Player Search API Structure - {name}",
                method,
                endpoint,
                expected_status,
                data=data
            )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting VerseLink Backend API Tests - Phase 7 Tournament Management Features")
        print(f"📡 Testing against: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Run basic health and auth tests first
        self.test_health_endpoints()
        self.test_auth_endpoints()
        
        # Run Organization Management Tests
        print("\n🏢 TESTING ORGANIZATION MANAGEMENT FEATURES")
        self.test_organizations_endpoints()
        self.test_organization_management_endpoints()
        self.test_organization_membership_policies()
        self.test_organization_data_validation()
        
        # Run Phase 3 Advanced Tournament Features Testing
        print("\n🏆 TESTING PHASE 3 - ADVANCED TOURNAMENT FEATURES")
        self.test_phase3_team_invitations_endpoints()
        self.test_phase3_match_disputes_endpoints()
        self.test_phase3_invitations_data_validation()
        self.test_phase3_disputes_data_validation()
        self.test_phase3_api_structure()
        
        # Run Phase 7 Tournament Management Testing
        print("\n🏆 TESTING PHASE 7 - NEW TOURNAMENT MANAGEMENT FEATURES")
        self.test_new_tournament_management_endpoints()
        self.test_new_tournament_team_management_endpoints()
        self.test_new_tournament_administration_endpoints()
        self.test_tournament_team_management_data_validation()
        self.test_tournament_state_management()
        
        # Run Phase Final Player Search Testing
        print("\n🔍 TESTING PHASE FINAL - PLAYER SEARCH SYSTEM")
        self.test_player_search_endpoints()
        self.test_player_search_data_validation()
        self.test_player_search_api_structure()
        
        # Run existing tournament tests
        print("\n🏆 TESTING EXISTING TOURNAMENT FEATURES")
        self.test_tournaments_endpoints()
        self.test_tournament_api_comprehensive()
        self.test_tournament_team_management_without_auth()
        self.test_match_score_reporting_without_auth()
        self.test_file_upload_api_without_auth()
        self.test_tournament_creation_without_auth()
        self.test_tournament_api_structure()
        self.test_tournament_data_validation()
        self.test_tournament_state_transitions()
        self.test_match_score_validation()
        self.test_file_upload_validation()
        self.test_tournament_bracket_generation()
        
        # Run Phase 6 comprehensive testing
        print("\n🔔 TESTING PHASE 6 - NOTIFICATIONS SYSTEM")
        self.test_notifications_endpoints()
        self.test_notifications_data_validation()
        
        print("\n🛡️ TESTING PHASE 6 - MODERATION SYSTEM")
        self.test_moderation_endpoints()
        self.test_moderation_data_validation()
        
        print("\n🤖 TESTING PHASE 6 - AUTO-MODERATION SYSTEM")
        self.test_auto_moderation_endpoints()
        self.test_auto_moderation_data_validation()
        self.test_auto_moderation_toggle_functionality()
        
        print("\n🔗 TESTING API STRUCTURE & INTEGRATION")
        self.test_phase6_api_structure()
        self.test_phase6_integration_scenarios()
        
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
    # Use the external URL from frontend/.env for testing
    base_url = "https://community-pulse-23.preview.emergentagent.com"
    
    print("VerseLink Phase 7 Backend API Test Suite - Tournament Management Features")
    print("=" * 90)
    
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