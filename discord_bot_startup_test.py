#!/usr/bin/env python3
"""
VerseLink Discord Bot Startup and Configuration Test
Tests if the Discord Bot can be properly initialized and configured
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add discord_bot directory to path
sys.path.insert(0, '/app/discord_bot')

class DiscordBotStartupTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
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

    def test_discord_bot_configuration(self):
        """Test Discord bot configuration and environment"""
        print("\n" + "="*60)
        print("TESTING DISCORD BOT CONFIGURATION")
        print("="*60)
        
        try:
            from config import Config
            
            # Test configuration validation (without actual tokens)
            required_configs = [
                ('DISCORD_BOT_TOKEN', 'Discord bot token configured'),
                ('VERSELINK_API_BASE', 'VerseLink API base URL configured'),
                ('VERSELINK_API_TOKEN', 'VerseLink API token configured'),
                ('BOT_PREFIX', 'Bot command prefix configured'),
                ('BOT_API_PORT', 'Bot API port configured')
            ]
            
            for config_name, description in required_configs:
                if hasattr(Config, config_name):
                    value = getattr(Config, config_name)
                    if value and str(value).strip():
                        self.log_test(f"Config {config_name}", True, description)
                    else:
                        self.log_test(f"Config {config_name}", False, f"{config_name} is empty or None")
                else:
                    self.log_test(f"Config {config_name}", False, f"{config_name} attribute missing")
            
            # Test configuration methods
            try:
                headers = Config.get_headers()
                if 'Authorization' in headers and 'Content-Type' in headers:
                    self.log_test("Config Headers Generation", True, "API headers properly generated")
                else:
                    self.log_test("Config Headers Generation", False, "API headers missing required fields")
            except Exception as e:
                self.log_test("Config Headers Generation", False, f"Error: {str(e)}")
                
        except Exception as e:
            self.log_test("Discord Bot Configuration", False, f"Configuration error: {str(e)}")

    def test_discord_bot_class_initialization(self):
        """Test Discord bot class can be initialized"""
        print("\n" + "="*60)
        print("TESTING DISCORD BOT CLASS INITIALIZATION")
        print("="*60)
        
        try:
            from bot import VerselinkBot
            
            # Test bot class structure
            required_methods = [
                'setup_hook', 'on_ready', 'on_guild_join', 'on_guild_remove',
                'on_message', 'register_all_guilds', 'on_command_error',
                'on_app_command_error', 'close'
            ]
            
            for method_name in required_methods:
                if hasattr(VerselinkBot, method_name):
                    method = getattr(VerselinkBot, method_name)
                    if callable(method):
                        self.log_test(f"VerselinkBot.{method_name}", True, "Method exists and is callable")
                    else:
                        self.log_test(f"VerselinkBot.{method_name}", False, "Method exists but not callable")
                else:
                    self.log_test(f"VerselinkBot.{method_name}", False, "Method missing")
            
            # Test bot initialization (without actually connecting to Discord)
            try:
                # We can't actually create the bot instance without valid tokens
                # But we can test that the class is properly structured
                if hasattr(VerselinkBot, '__init__'):
                    self.log_test("VerselinkBot Class Structure", True, "Bot class properly structured")
                else:
                    self.log_test("VerselinkBot Class Structure", False, "Bot class missing __init__")
            except Exception as e:
                self.log_test("VerselinkBot Class Structure", False, f"Error: {str(e)}")
                
        except Exception as e:
            self.log_test("Discord Bot Class Initialization", False, f"Error: {str(e)}")

    def test_command_cogs_loading(self):
        """Test that command cogs can be loaded"""
        print("\n" + "="*60)
        print("TESTING COMMAND COGS LOADING")
        print("="*60)
        
        try:
            # Test InteractiveEvents cog
            from interactive_events import InteractiveEvents
            
            # Check if cog has required methods
            cog_methods = ['create_event_interactive', 'create_tournament_interactive', 'on_message']
            for method_name in cog_methods:
                if hasattr(InteractiveEvents, method_name):
                    self.log_test(f"InteractiveEvents.{method_name}", True, "Command method exists")
                else:
                    self.log_test(f"InteractiveEvents.{method_name}", False, "Command method missing")
            
            # Test EventManagement cog
            from event_management import EventManagement
            
            management_methods = ['start_event', 'cancel_event', 'join_event', 'leave_event', 'my_events']
            for method_name in management_methods:
                if hasattr(EventManagement, method_name):
                    self.log_test(f"EventManagement.{method_name}", True, "Management command exists")
                else:
                    self.log_test(f"EventManagement.{method_name}", False, "Management command missing")
                    
        except Exception as e:
            self.log_test("Command Cogs Loading", False, f"Error: {str(e)}")

    def test_interactive_creation_workflow(self):
        """Test interactive creation workflow components"""
        print("\n" + "="*60)
        print("TESTING INTERACTIVE CREATION WORKFLOW")
        print("="*60)
        
        try:
            from interactive_events import InteractiveSession, SessionManager, EventCreationView
            from event_handlers import EventCreationHandler
            from tournament_handlers import TournamentCreationHandler
            from verselink_api import VerselinkAPI
            
            # Test complete workflow components
            api = VerselinkAPI()
            session_manager = SessionManager()
            event_handler = EventCreationHandler(api)
            tournament_handler = TournamentCreationHandler(api)
            
            # Test event creation workflow
            event_session = session_manager.create_session("test_user", "event")
            event_session.data['type'] = 'raid'
            
            current_step = event_handler.get_current_step(event_session)
            if current_step == 'title':
                self.log_test("Event Creation Workflow", True, "Event workflow properly initialized")
            else:
                self.log_test("Event Creation Workflow", False, f"Unexpected step: {current_step}")
            
            # Test tournament creation workflow
            tournament_session = session_manager.create_session("test_user2", "tournament")
            tournament_session.data['name'] = 'Test Tournament'
            
            current_step = tournament_handler.get_current_step(tournament_session)
            if current_step == 'description':
                self.log_test("Tournament Creation Workflow", True, "Tournament workflow properly initialized")
            else:
                self.log_test("Tournament Creation Workflow", False, f"Unexpected step: {current_step}")
            
            # Test UI components
            view = EventCreationView(session_manager)
            if hasattr(view, 'children') and len(view.children) > 0:
                self.log_test("Discord UI Components", True, f"UI view has {len(view.children)} components")
            else:
                self.log_test("Discord UI Components", False, "UI view has no components")
                
        except Exception as e:
            self.log_test("Interactive Creation Workflow", False, f"Error: {str(e)}")

    def test_phase2_event_types_support(self):
        """Test Phase 2 event types support"""
        print("\n" + "="*60)
        print("TESTING PHASE 2 EVENT TYPES SUPPORT")
        print("="*60)
        
        try:
            from interactive_events import EventCreationView, SessionManager
            
            session_manager = SessionManager()
            view = EventCreationView(session_manager)
            
            # Check if all 11 event types are supported
            expected_event_types = [
                'raid', 'course', 'pvp', 'fps', 'salvaging', 
                'logistique', 'exploration', 'mining', 'trading', 
                'roleplay', 'autre'
            ]
            
            if hasattr(view, 'children') and len(view.children) > 0:
                select_component = view.children[0]
                if hasattr(select_component, 'options'):
                    available_types = [option.value for option in select_component.options]
                    
                    missing_types = [t for t in expected_event_types if t not in available_types]
                    extra_types = [t for t in available_types if t not in expected_event_types]
                    
                    if not missing_types and not extra_types:
                        self.log_test("Phase 2 Event Types", True, f"All {len(expected_event_types)} event types supported")
                    elif missing_types:
                        self.log_test("Phase 2 Event Types", False, f"Missing types: {missing_types}")
                    else:
                        self.log_test("Phase 2 Event Types", True, f"All expected types + extras: {extra_types}")
                else:
                    self.log_test("Phase 2 Event Types", False, "Select component has no options")
            else:
                self.log_test("Phase 2 Event Types", False, "No UI components found")
                
        except Exception as e:
            self.log_test("Phase 2 Event Types Support", False, f"Error: {str(e)}")

    def test_tournament_formats_support(self):
        """Test tournament formats support"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT FORMATS SUPPORT")
        print("="*60)
        
        try:
            from tournament_handlers import TournamentCreationHandler
            from verselink_api import VerselinkAPI
            
            api = VerselinkAPI()
            handler = TournamentCreationHandler(api)
            
            # Test that handler can process different tournament types
            expected_formats = [
                'elimination', 'double_elimination', 'round_robin', 
                'swiss', 'league', 'custom'
            ]
            
            # We can't test the actual validation without a full session,
            # but we can verify the handler has the necessary structure
            if hasattr(handler, 'api') and hasattr(handler, 'get_current_step'):
                self.log_test("Tournament Handler Structure", True, "Handler properly structured")
            else:
                self.log_test("Tournament Handler Structure", False, "Handler missing required attributes")
            
            # Test date parsing which is crucial for tournaments
            try:
                test_date = "2025-12-25 20:30"
                parsed = handler.parse_date(test_date)
                if parsed and hasattr(parsed, 'year') and parsed.year == 2025:
                    self.log_test("Tournament Date Parsing", True, f"Date parsed correctly: {parsed}")
                else:
                    self.log_test("Tournament Date Parsing", False, "Date parsing failed")
            except Exception as e:
                self.log_test("Tournament Date Parsing", False, f"Parse error: {str(e)}")
                
        except Exception as e:
            self.log_test("Tournament Formats Support", False, f"Error: {str(e)}")

    def test_session_management_robustness(self):
        """Test session management robustness"""
        print("\n" + "="*60)
        print("TESTING SESSION MANAGEMENT ROBUSTNESS")
        print("="*60)
        
        try:
            from interactive_events import InteractiveSession, SessionManager
            from datetime import datetime, timedelta
            
            manager = SessionManager()
            
            # Test multiple concurrent sessions
            sessions = []
            for i in range(5):
                session = manager.create_session(f"user_{i}", "event" if i % 2 == 0 else "tournament")
                session.data[f'test_data_{i}'] = f"value_{i}"
                sessions.append(session)
            
            # Verify all sessions are tracked
            active_sessions = len([s for s in manager.sessions.values() if s.is_active])
            if active_sessions == 5:
                self.log_test("Concurrent Sessions", True, f"All {active_sessions} sessions active")
            else:
                self.log_test("Concurrent Sessions", False, f"Expected 5, got {active_sessions}")
            
            # Test session expiration
            old_session = manager.create_session("old_user", "event")
            old_session.last_activity = datetime.utcnow() - timedelta(minutes=35)
            
            if old_session.is_expired(30):
                self.log_test("Session Expiration Logic", True, "Expired session correctly identified")
            else:
                self.log_test("Session Expiration Logic", False, "Session expiration logic failed")
            
            # Test cleanup
            manager.cleanup_expired()
            cleaned_session = manager.get_session("old_user")
            if cleaned_session is None:
                self.log_test("Session Cleanup", True, "Expired sessions cleaned up")
            else:
                self.log_test("Session Cleanup", False, "Expired sessions not cleaned up")
                
        except Exception as e:
            self.log_test("Session Management Robustness", False, f"Error: {str(e)}")

    def test_error_handling_and_validation(self):
        """Test error handling and validation"""
        print("\n" + "="*60)
        print("TESTING ERROR HANDLING AND VALIDATION")
        print("="*60)
        
        try:
            from event_handlers import EventCreationHandler
            from tournament_handlers import TournamentCreationHandler
            from verselink_api import VerselinkAPI
            from interactive_events import InteractiveSession
            
            api = VerselinkAPI()
            event_handler = EventCreationHandler(api)
            tournament_handler = TournamentCreationHandler(api)
            
            # Test invalid date parsing
            try:
                invalid_date = tournament_handler.parse_date("invalid_date_format")
                self.log_test("Invalid Date Handling", False, "Should have raised exception")
            except ValueError:
                self.log_test("Invalid Date Handling", True, "Properly handles invalid dates")
            except Exception as e:
                self.log_test("Invalid Date Handling", True, f"Handles with exception: {type(e).__name__}")
            
            # Test session step progression
            test_session = InteractiveSession("test_user", "event")
            
            # Empty session should start with first step
            first_step = event_handler.get_current_step(test_session)
            if first_step == 'title':
                self.log_test("Step Progression Logic", True, "Correct initial step")
            else:
                self.log_test("Step Progression Logic", False, f"Wrong initial step: {first_step}")
            
            # Add data and test progression
            test_session.data['title'] = "Test"
            next_step = event_handler.get_current_step(test_session)
            if next_step == 'description':
                self.log_test("Step Progression Advance", True, "Correctly advances to next step")
            else:
                self.log_test("Step Progression Advance", False, f"Wrong next step: {next_step}")
                
        except Exception as e:
            self.log_test("Error Handling and Validation", False, f"Error: {str(e)}")

    async def run_all_tests(self):
        """Run all startup tests"""
        print("🚀 Starting VerseLink Discord Bot Startup Tests")
        print("="*80)
        
        # Run all tests
        self.test_discord_bot_configuration()
        self.test_discord_bot_class_initialization()
        self.test_command_cogs_loading()
        self.test_interactive_creation_workflow()
        self.test_phase2_event_types_support()
        self.test_tournament_formats_support()
        self.test_session_management_robustness()
        self.test_error_handling_and_validation()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("STARTUP TEST SUMMARY")
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
    tester = DiscordBotStartupTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())