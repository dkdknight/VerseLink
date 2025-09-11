#!/usr/bin/env python3
"""
Critical Issues Test - Focus on Discord Bot and Organization Creation Issues
Tests the specific issues mentioned in the review request
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CriticalIssuesTester:
    def __init__(self, base_url: str = "https://org-admin-revamp.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_issues = []
        self.error_messages = []

    def log_critical_issue(self, endpoint: str, issue: str, error_details: str = ""):
        """Log critical issue found"""
        self.critical_issues.append({
            "endpoint": endpoint,
            "issue": issue,
            "error_details": error_details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"🚨 CRITICAL ISSUE - {endpoint}: {issue}")
        if error_details:
            print(f"    Error Details: {error_details}")

    def test_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, expected_status: int = None) -> tuple[int, Dict, str]:
        """Make test request and return status, response, error"""
        url = f"{self.base_url}{endpoint}"
        
        # Default headers
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)

        print(f"\n🔍 Testing {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=10)
            else:
                return 500, {}, f"Unsupported method: {method}"

            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            print(f"    Status: {response.status_code}")
            if response.status_code >= 400:
                print(f"    Response: {response.text[:300]}")

            return response.status_code, response_data, ""

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            return 500, {}, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"    ❌ {error_msg}")
            return 500, {}, error_msg

    def test_discord_bot_endpoints(self):
        """Test Discord Bot Integration Issues"""
        print("\n" + "="*80)
        print("🤖 TESTING DISCORD BOT INTEGRATION ISSUES")
        print("="*80)
        
        # Test 1: Discord Bot Verify Endpoint
        print("\n--- Testing Discord Bot Verify Endpoint ---")
        
        # Test with POST data (as expected by bot)
        bot_verify_data = {
            "guild_id": "123456789012345678",
            "api_key": "test-api-key"
        }
        
        status, response, error = self.test_request(
            "POST", 
            "/api/v1/discord/bot/verify", 
            data=bot_verify_data
        )
        
        if status == 500 or error:
            self.log_critical_issue(
                "/api/v1/discord/bot/verify",
                "Endpoint returning 500 error or connection failure",
                f"Status: {status}, Error: {error}, Response: {response}"
            )
        elif status == 404:
            self.log_critical_issue(
                "/api/v1/discord/bot/verify",
                "Endpoint not found - possible routing issue",
                f"Status: {status}, Response: {response}"
            )
        elif status not in [200, 401, 403]:
            self.log_critical_issue(
                "/api/v1/discord/bot/verify",
                f"Unexpected status code: {status}",
                f"Response: {response}"
            )
        
        # Test 2: Guild Registration Endpoint
        print("\n--- Testing Discord Guild Registration Endpoint ---")
        
        guild_data = {
            "guild_name": "Test Guild",
            "guild_icon": "https://example.com/icon.png",
            "owner_id": "987654321098765432",
            "member_count": 150,
            "setup_by_user_id": "user123",
            "bot_auto_registered": True
        }
        
        status, response, error = self.test_request(
            "POST", 
            "/api/v1/discord/bot/guild/123456789012345678/register", 
            data=guild_data
        )
        
        if status == 500 or error:
            self.log_critical_issue(
                "/api/v1/discord/bot/guild/{guild_id}/register",
                "Guild registration endpoint failing",
                f"Status: {status}, Error: {error}, Response: {response}"
            )
        elif status == 404:
            self.log_critical_issue(
                "/api/v1/discord/bot/guild/{guild_id}/register",
                "Guild registration endpoint not found",
                f"Status: {status}, Response: {response}"
            )
        
        # Test 3: Guild Config Endpoint
        print("\n--- Testing Discord Guild Config Endpoint ---")
        
        # Test with query parameter (as mentioned in test_result.md)
        status, response, error = self.test_request(
            "GET", 
            "/api/v1/discord/bot/guild/123456789012345678/config?api_key=test-key"
        )
        
        if status == 500 or error:
            self.log_critical_issue(
                "/api/v1/discord/bot/guild/{guild_id}/config",
                "Guild config endpoint failing",
                f"Status: {status}, Error: {error}, Response: {response}"
            )
        elif status == 404:
            self.log_critical_issue(
                "/api/v1/discord/bot/guild/{guild_id}/config",
                "Guild config endpoint not found",
                f"Status: {status}, Response: {response}"
            )
        
        # Test with body parameter (alternative approach)
        config_data = {
            "api_key": "test-key"
        }
        
        status, response, error = self.test_request(
            "POST", 
            "/api/v1/discord/bot/guild/123456789012345678/config", 
            data=config_data
        )
        
        if status == 404:
            print("    ℹ️  POST method not supported for config endpoint (expected)")
        elif status == 405:
            print("    ℹ️  Method not allowed (expected for GET-only endpoint)")

    def test_organization_creation(self):
        """Test Organization Creation Issues"""
        print("\n" + "="*80)
        print("🏢 TESTING ORGANIZATION CREATION ISSUES")
        print("="*80)
        
        # Test 1: Organization Creation Endpoint
        print("\n--- Testing Organization Creation Endpoint ---")
        
        org_data = {
            "name": "Test Star Citizen Corporation",
            "tag": "TSC",
            "description": "A test corporation for Star Citizen operations and events",
            "visibility": "public",
            "website": "https://testcorp.example.com",
            "discord_server": "https://discord.gg/testcorp",
            "logo_url": "https://example.com/logo.png",
            "banner_url": "https://example.com/banner.png"
        }
        
        status, response, error = self.test_request(
            "POST", 
            "/api/v1/orgs/", 
            data=org_data
        )
        
        if status == 500 or error:
            self.log_critical_issue(
                "POST /api/v1/orgs/",
                "Organization creation endpoint returning 500 error",
                f"Status: {status}, Error: {error}, Response: {response}"
            )
        elif status == 404:
            self.log_critical_issue(
                "POST /api/v1/orgs/",
                "Organization creation endpoint not found",
                f"Status: {status}, Response: {response}"
            )
        elif status == 403:
            print("    ✅ Expected 403 (authentication required)")
        elif status not in [200, 201, 401, 403]:
            self.log_critical_issue(
                "POST /api/v1/orgs/",
                f"Unexpected status code: {status}",
                f"Response: {response}"
            )
        
        # Test 2: Organization List Endpoint (should work without auth)
        print("\n--- Testing Organization List Endpoint ---")
        
        status, response, error = self.test_request("GET", "/api/v1/orgs/")
        
        if status == 500 or error:
            self.log_critical_issue(
                "GET /api/v1/orgs/",
                "Organization list endpoint failing",
                f"Status: {status}, Error: {error}, Response: {response}"
            )
        elif status == 404:
            self.log_critical_issue(
                "GET /api/v1/orgs/",
                "Organization list endpoint not found",
                f"Status: {status}, Response: {response}"
            )
        elif status == 200:
            print("    ✅ Organization list endpoint working")
            if isinstance(response, list):
                print(f"    📊 Returned {len(response)} organizations")
            else:
                print(f"    ⚠️  Response format: {type(response)}")

    def test_database_connectivity(self):
        """Test Database Connectivity Issues"""
        print("\n" + "="*80)
        print("🗄️  TESTING DATABASE CONNECTIVITY")
        print("="*80)
        
        # Test endpoints that should indicate database connectivity
        endpoints_to_test = [
            ("GET", "/api/v1/health", "Health check endpoint"),
            ("GET", "/api/v1/orgs/", "Organizations list (database read)"),
            ("GET", "/api/v1/events/", "Events list (database read)"),
            ("GET", "/api/v1/tournaments/", "Tournaments list (database read)")
        ]
        
        for method, endpoint, description in endpoints_to_test:
            print(f"\n--- Testing {description} ---")
            
            status, response, error = self.test_request(method, endpoint)
            
            if status == 500 or error:
                self.log_critical_issue(
                    endpoint,
                    f"Database connectivity issue - {description}",
                    f"Status: {status}, Error: {error}, Response: {response}"
                )
            elif status == 200:
                print(f"    ✅ {description} working")
            else:
                print(f"    ℹ️  Status: {status} (may be expected)")

    def test_environment_variables(self):
        """Test Environment Variable Configuration"""
        print("\n" + "="*80)
        print("🔧 TESTING ENVIRONMENT VARIABLE CONFIGURATION")
        print("="*80)
        
        # Test Discord integration health (should indicate if Discord env vars are set)
        print("\n--- Testing Discord Integration Health ---")
        
        status, response, error = self.test_request("GET", "/api/v1/discord/health")
        
        if status == 200 and isinstance(response, dict):
            print("    ✅ Discord health endpoint working")
            
            # Check for configuration indicators
            config_indicators = [
                "webhook_secret_configured",
                "bot_api_configured", 
                "guilds_registered",
                "active_guilds"
            ]
            
            for indicator in config_indicators:
                if indicator in response:
                    print(f"    📊 {indicator}: {response[indicator]}")
                else:
                    print(f"    ⚠️  Missing indicator: {indicator}")
                    
            if response.get("status") != "healthy":
                self.log_critical_issue(
                    "/api/v1/discord/health",
                    "Discord integration not healthy",
                    f"Status: {response.get('status')}, Response: {response}"
                )
        elif status == 500 or error:
            self.log_critical_issue(
                "/api/v1/discord/health",
                "Discord health endpoint failing",
                f"Status: {status}, Error: {error}, Response: {response}"
            )

    def test_service_startup_issues(self):
        """Test for Service Startup Issues"""
        print("\n" + "="*80)
        print("🚀 TESTING SERVICE STARTUP ISSUES")
        print("="*80)
        
        # Test main health endpoint
        print("\n--- Testing Main Health Endpoint ---")
        
        status, response, error = self.test_request("GET", "/api/v1/health")
        
        if status != 200:
            self.log_critical_issue(
                "/api/v1/health",
                "Main health endpoint not responding correctly",
                f"Status: {status}, Error: {error}, Response: {response}"
            )
        else:
            print("    ✅ Main health endpoint working")
        
        # Test root endpoint
        print("\n--- Testing Root Endpoint ---")
        
        status, response, error = self.test_request("GET", "/")
        
        if status != 200:
            self.log_critical_issue(
                "/",
                "Root endpoint not responding correctly",
                f"Status: {status}, Error: {error}, Response: {response}"
            )
        else:
            print("    ✅ Root endpoint working")
            if isinstance(response, dict) and "message" in response:
                print(f"    📝 Message: {response['message']}")

    def run_all_tests(self):
        """Run all critical issue tests"""
        print("🔍 VERSELINK CRITICAL ISSUES TESTING")
        print("="*80)
        print(f"📡 Testing against: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Run all test categories
        self.test_discord_bot_endpoints()
        self.test_organization_creation()
        self.test_database_connectivity()
        self.test_environment_variables()
        self.test_service_startup_issues()
        
        # Print summary
        print("\n" + "="*80)
        print("📊 CRITICAL ISSUES SUMMARY")
        print("="*80)
        
        if not self.critical_issues:
            print("✅ No critical issues found!")
        else:
            print(f"🚨 Found {len(self.critical_issues)} critical issues:")
            
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"\n{i}. {issue['endpoint']}")
                print(f"   Issue: {issue['issue']}")
                if issue['error_details']:
                    print(f"   Details: {issue['error_details']}")
        
        print(f"\n⏰ Completed at: {datetime.now().isoformat()}")
        
        return self.critical_issues

if __name__ == "__main__":
    tester = CriticalIssuesTester()
    critical_issues = tester.run_all_tests()
    
    # Exit with error code if critical issues found
    sys.exit(1 if critical_issues else 0)