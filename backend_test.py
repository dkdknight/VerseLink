#!/usr/bin/env python3
"""
VerseLink Backend API Test Suite
Tests all Phase 1 endpoints for VerseLink application
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class VerselinkAPITester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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

    def test_notifications_endpoints_comprehensive(self):
        """Test Phase 4 notifications endpoints comprehensively"""
        print("\n" + "="*50)
        print("TESTING PHASE 4 NOTIFICATIONS ENDPOINTS - COMPREHENSIVE")
        print("="*50)
        
        # Test endpoints without authentication (should fail with 403)
        self.run_test(
            "Get Notifications Without Auth",
            "GET",
            "/api/v1/notifications/me",
            403
        )
        
        self.run_test(
            "Get Notification Stats Without Auth",
            "GET",
            "/api/v1/notifications/me/stats",
            403
        )
        
        self.run_test(
            "Mark Notification Read Without Auth",
            "POST",
            "/api/v1/notifications/test-notification-id/read",
            403
        )
        
        self.run_test(
            "Mark All Notifications Read Without Auth",
            "POST",
            "/api/v1/notifications/me/read-all",
            403
        )
        
        self.run_test(
            "Get Notification Preferences Without Auth",
            "GET",
            "/api/v1/notifications/me/preferences",
            403
        )
        
        self.run_test(
            "Update Notification Preferences Without Auth",
            "PUT",
            "/api/v1/notifications/me/preferences",
            403,
            data={"preferences": {}}
        )
        
        self.run_test(
            "Create Test Notification Without Auth",
            "POST",
            "/api/v1/notifications/test",
            403
        )
        
        # Test with invalid token
        print("\n🔍 Testing with invalid token...")
        invalid_token = "invalid.jwt.token"
        
        self.run_test(
            "Get Notifications With Invalid Token",
            "GET",
            "/api/v1/notifications/me",
            401,  # Invalid token returns 401, not 403
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        # Test notification preferences with invalid data
        self.run_test(
            "Update Preferences With Invalid Data Structure",
            "PUT",
            "/api/v1/notifications/me/preferences",
            403,  # Will fail auth first, but tests the endpoint exists
            data={"invalid": "structure"}
        )

    def test_moderation_endpoints_comprehensive(self):
        """Test Phase 4 moderation endpoints comprehensively"""
        print("\n" + "="*50)
        print("TESTING PHASE 4 MODERATION ENDPOINTS - COMPREHENSIVE")
        print("="*50)
        
        # Test endpoints without authentication (should fail with 403)
        self.run_test(
            "Create Report Without Auth",
            "POST",
            "/api/v1/moderation/reports",
            403,
            data={
                "reported_user_id": "test-user-id",
                "type": "spam",
                "reason": "This user is posting spam messages repeatedly in chat channels."
            }
        )
        
        self.run_test(
            "List Reports Without Auth",
            "GET",
            "/api/v1/moderation/reports",
            403
        )
        
        self.run_test(
            "Get Report Without Auth",
            "GET",
            "/api/v1/moderation/reports/test-report-id",
            403
        )
        
        self.run_test(
            "Handle Report Without Auth",
            "POST",
            "/api/v1/moderation/reports/test-report-id/action",
            403,
            data={
                "action": "warning",
                "reason": "First offense warning"
            }
        )
        
        self.run_test(
            "Get User Moderation History Without Auth",
            "GET",
            "/api/v1/moderation/users/test-user-id/history",
            403
        )
        
        self.run_test(
            "Get Moderation Stats Without Auth",
            "GET",
            "/api/v1/moderation/stats",
            403
        )
        
        self.run_test(
            "Get Audit Logs Without Auth",
            "GET",
            "/api/v1/moderation/audit-logs",
            403
        )
        
        self.run_test(
            "Unban Expired Users Without Auth",
            "POST",
            "/api/v1/moderation/maintenance/unban-expired",
            403
        )
        
        # Test with invalid token
        print("\n🔍 Testing moderation with invalid token...")
        invalid_token = "invalid.jwt.token"
        
        self.run_test(
            "Create Report With Invalid Token",
            "POST",
            "/api/v1/moderation/reports",
            403,
            data={
                "reported_user_id": "test-user-id",
                "type": "harassment",
                "reason": "User is harassing other players in voice chat."
            },
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        # Test report creation with invalid data
        self.run_test(
            "Create Report With Invalid Data - Missing Reason",
            "POST",
            "/api/v1/moderation/reports",
            403,  # Will fail auth first, but tests the endpoint exists
            data={
                "reported_user_id": "test-user-id",
                "type": "spam"
                # Missing required 'reason' field
            }
        )
        
        self.run_test(
            "Create Report With Invalid Data - Short Reason",
            "POST",
            "/api/v1/moderation/reports",
            403,  # Will fail auth first, but tests the endpoint exists
            data={
                "reported_user_id": "test-user-id",
                "type": "spam",
                "reason": "short"  # Too short (min 10 chars)
            }
        )
        
        # Test moderation action with invalid data
        self.run_test(
            "Handle Report With Invalid Action",
            "POST",
            "/api/v1/moderation/reports/test-report-id/action",
            403,  # Will fail auth first, but tests the endpoint exists
            data={
                "action": "invalid_action",
                "reason": "Test reason"
            }
        )
        
        # Test pagination parameters
        self.run_test(
            "List Reports With Pagination",
            "GET",
            "/api/v1/moderation/reports?limit=10&skip=0",
            403
        )
        
        self.run_test(
            "List Reports With Status Filter",
            "GET",
            "/api/v1/moderation/reports?status=pending",
            403
        )
        
        self.run_test(
            "Get Audit Logs With Pagination",
            "GET",
            "/api/v1/moderation/audit-logs?limit=25&skip=0",
            403
        )

    def test_phase4_api_structure(self):
        """Test Phase 4 API structure and endpoint availability"""
        print("\n" + "="*50)
        print("TESTING PHASE 4 API STRUCTURE")
        print("="*50)
        
        # Test that all Phase 4 endpoints exist and return proper error codes
        phase4_endpoints = [
            # Notifications endpoints
            ("GET", "/api/v1/notifications/me", "Notifications List"),
            ("GET", "/api/v1/notifications/me/stats", "Notification Stats"),
            ("POST", "/api/v1/notifications/test-id/read", "Mark Notification Read"),
            ("POST", "/api/v1/notifications/me/read-all", "Mark All Read"),
            ("GET", "/api/v1/notifications/me/preferences", "Get Preferences"),
            ("PUT", "/api/v1/notifications/me/preferences", "Update Preferences"),
            ("POST", "/api/v1/notifications/test", "Test Notification"),
            
            # Moderation endpoints
            ("POST", "/api/v1/moderation/reports", "Create Report"),
            ("GET", "/api/v1/moderation/reports", "List Reports"),
            ("GET", "/api/v1/moderation/reports/test-id", "Get Report"),
            ("POST", "/api/v1/moderation/reports/test-id/action", "Handle Report"),
            ("GET", "/api/v1/moderation/users/test-id/history", "User History"),
            ("GET", "/api/v1/moderation/stats", "Moderation Stats"),
            ("GET", "/api/v1/moderation/audit-logs", "Audit Logs"),
            ("POST", "/api/v1/moderation/maintenance/unban-expired", "Unban Expired"),
        ]
        
        for method, endpoint, name in phase4_endpoints:
            # All should return 403 (auth required) rather than 404 (not found)
            expected_status = 403
            data = {} if method in ["POST", "PUT"] else None
            
            self.run_test(
                f"API Structure - {name}",
                method,
                endpoint,
                expected_status,
                data=data
            )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting VerseLink Backend API Tests - Phase 4 Focus")
        print(f"📡 Testing against: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Run test suites
        self.test_health_endpoints()
        self.test_auth_endpoints()
        self.test_organizations_endpoints()
        self.test_users_endpoints()
        self.test_events_endpoints()
        self.test_tournaments_endpoints()
        self.test_discord_integration_endpoints()
        
        # Phase 4 comprehensive testing
        self.test_notifications_endpoints_comprehensive()
        self.test_moderation_endpoints_comprehensive()
        self.test_phase4_api_structure()
        
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