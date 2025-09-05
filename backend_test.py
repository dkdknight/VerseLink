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
            401
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
            "/api/v1/users/profile",
            401
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
            401,
            data={"role_id": None, "notes": "Test signup"}
        )
        
        self.run_test(
            "Withdraw Without Auth",
            "DELETE",
            f"/api/v1/events/{test_event_id}/signups/me",
            401
        )
        
        self.run_test(
            "Checkin Without Auth",
            "POST",
            f"/api/v1/events/{test_event_id}/checkin",
            401
        )
        
        # Test create event without auth (should fail)
        self.run_test(
            "Create Event Without Auth",
            "POST",
            "/api/v1/orgs/test-org/events",
            401,
            data={
                "title": "Test Event",
                "description": "Test event description",
                "type": "raid",
                "start_at_utc": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "duration_minutes": 120
            }
        )

    def test_tournaments_endpoints(self):
        """Test tournaments endpoints"""
        print("\n" + "="*50)
        print("TESTING TOURNAMENTS ENDPOINTS")
        print("="*50)
        
        # Test tournaments listing
        self.run_test(
            "List Tournaments",
            "GET",
            "/api/v1/tournaments/",
            200
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

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting VerseLink Backend API Tests")
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
    base_url = "http://localhost:8001"
    
    print("VerseLink Phase 2 Backend API Test Suite - Event System")
    print("=" * 60)
    
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