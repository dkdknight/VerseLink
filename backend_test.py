#!/usr/bin/env python3
"""
VerseLink Backend API Test Suite - Phase 4 Tournament System Testing
Tests Tournament & Brackets system for VerseLink application
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
        """Test Discord integration endpoints"""
        print("\n" + "="*50)
        print("TESTING DISCORD INTEGRATION ENDPOINTS")
        print("="*50)
        
        # Test webhook endpoints (should accept POST)
        self.run_test(
            "Discord Event Announce Webhook",
            "POST",
            "/api/v1/integrations/discord/events/announce",
            200,
            data={"test": "payload"}
        )
        
        self.run_test(
            "Discord Match Announce Webhook", 
            "POST",
            "/api/v1/integrations/discord/matches/announce",
            200,
            data={"test": "payload"}
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
        print("🚀 Starting VerseLink Backend API Tests - Phase 4 Tournament System")
        print(f"📡 Testing against: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Run basic health and auth tests first
        self.test_health_endpoints()
        self.test_auth_endpoints()
        
        # Run comprehensive tournament system tests
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
        self.test_authentication_edge_cases()
        
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
    
    print("VerseLink Phase 4 Backend API Test Suite - Notifications & Moderation")
    print("=" * 70)
    
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