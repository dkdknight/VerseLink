#!/usr/bin/env python3
"""
VerseLink Discord Bot Phase 2 Test Suite
Tests the interactive event and tournament creation system
"""

import sys
import os
import asyncio
import importlib.util
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

# Add discord_bot directory to path
sys.path.insert(0, '/app/discord_bot')

class DiscordBotPhase2Tester:
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

    def test_module_imports(self):
        """Test that all Discord bot modules can be imported"""
        print("\n" + "="*60)
        print("TESTING MODULE IMPORTS")
        print("="*60)
        
        modules_to_test = [
            ('config', '/app/discord_bot/config.py'),
            ('utils', '/app/discord_bot/utils.py'),
            ('verselink_api', '/app/discord_bot/verselink_api.py'),
            ('interactive_events', '/app/discord_bot/interactive_events.py'),
            ('event_handlers', '/app/discord_bot/event_handlers.py'),
            ('tournament_handlers', '/app/discord_bot/tournament_handlers.py'),
            ('event_management', '/app/discord_bot/event_management.py'),
            ('bot', '/app/discord_bot/bot.py')
        ]
        
        for module_name, module_path in modules_to_test:
            try:
                if os.path.exists(module_path):
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.log_test(f"Import {module_name}", True, f"Module loaded from {module_path}")
                else:
                    self.log_test(f"Import {module_name}", False, f"Module file not found: {module_path}")
            except Exception as e:
                self.log_test(f"Import {module_name}", False, f"Import error: {str(e)}")

    def test_configuration_validation(self):
        """Test Discord bot configuration"""
        print("\n" + "="*60)
        print("TESTING CONFIGURATION")
        print("="*60)
        
        try:
            from config import Config
            
            # Test configuration attributes exist
            required_attrs = [
                'DISCORD_BOT_TOKEN', 'VERSELINK_API_BASE', 'VERSELINK_API_TOKEN',
                'BOT_PREFIX', 'DEBUG_MODE', 'LOG_LEVEL', 'ENVIRONMENT',
                'BOT_API_PORT', 'BOT_API_TOKEN'
            ]
            
            for attr in required_attrs:
                if hasattr(Config, attr):
                    self.log_test(f"Config.{attr}", True, f"Attribute exists")
                else:
                    self.log_test(f"Config.{attr}", False, f"Missing required attribute")
            
            # Test configuration methods
            try:
                headers = Config.get_headers()
                if isinstance(headers, dict) and 'Authorization' in headers:
                    self.log_test("Config.get_headers()", True, "Headers method works")
                else:
                    self.log_test("Config.get_headers()", False, "Headers method returns invalid format")
            except Exception as e:
                self.log_test("Config.get_headers()", False, f"Headers method error: {str(e)}")
            
            try:
                site_base = Config.get_site_base()
                if isinstance(site_base, str) and site_base.startswith('http'):
                    self.log_test("Config.get_site_base()", True, f"Site base: {site_base}")
                else:
                    self.log_test("Config.get_site_base()", False, "Site base method returns invalid format")
            except Exception as e:
                self.log_test("Config.get_site_base()", False, f"Site base method error: {str(e)}")
                
        except Exception as e:
            self.log_test("Configuration Loading", False, f"Failed to load config: {str(e)}")

    def test_interactive_session_classes(self):
        """Test interactive session management classes"""
        print("\n" + "="*60)
        print("TESTING INTERACTIVE SESSION CLASSES")
        print("="*60)
        
        try:
            from interactive_events import InteractiveSession, SessionManager
            
            # Test InteractiveSession creation
            session = InteractiveSession("test_user_123", "event")
            
            if session.user_id == "test_user_123":
                self.log_test("InteractiveSession.user_id", True, "User ID set correctly")
            else:
                self.log_test("InteractiveSession.user_id", False, "User ID not set correctly")
            
            if session.session_type == "event":
                self.log_test("InteractiveSession.session_type", True, "Session type set correctly")
            else:
                self.log_test("InteractiveSession.session_type", False, "Session type not set correctly")
            
            if hasattr(session, 'session_id') and session.session_id:
                self.log_test("InteractiveSession.session_id", True, f"Session ID generated: {session.session_id[:8]}...")
            else:
                self.log_test("InteractiveSession.session_id", False, "Session ID not generated")
            
            # Test session activity update
            original_activity = session.last_activity
            session.update_activity()
            if session.last_activity > original_activity:
                self.log_test("InteractiveSession.update_activity()", True, "Activity timestamp updated")
            else:
                self.log_test("InteractiveSession.update_activity()", False, "Activity timestamp not updated")
            
            # Test SessionManager
            manager = SessionManager()
            
            # Test session creation
            new_session = manager.create_session("test_user_456", "tournament")
            if new_session.user_id == "test_user_456" and new_session.session_type == "tournament":
                self.log_test("SessionManager.create_session()", True, "Session created successfully")
            else:
                self.log_test("SessionManager.create_session()", False, "Session creation failed")
            
            # Test session retrieval
            retrieved_session = manager.get_session("test_user_456")
            if retrieved_session and retrieved_session.session_id == new_session.session_id:
                self.log_test("SessionManager.get_session()", True, "Session retrieved successfully")
            else:
                self.log_test("SessionManager.get_session()", False, "Session retrieval failed")
            
            # Test session ending
            manager.end_session(new_session.session_id)
            ended_session = manager.get_session("test_user_456")
            if ended_session is None:
                self.log_test("SessionManager.end_session()", True, "Session ended successfully")
            else:
                self.log_test("SessionManager.end_session()", False, "Session not ended properly")
                
        except Exception as e:
            self.log_test("Interactive Session Classes", False, f"Error testing session classes: {str(e)}")

    def test_event_handlers(self):
        """Test event creation handlers"""
        print("\n" + "="*60)
        print("TESTING EVENT HANDLERS")
        print("="*60)
        
        try:
            from event_handlers import EventCreationHandler
            from verselink_api import VerselinkAPI
            
            # Test EventCreationHandler creation
            api = VerselinkAPI()
            handler = EventCreationHandler(api)
            
            if hasattr(handler, 'api') and handler.api == api:
                self.log_test("EventCreationHandler.__init__()", True, "Handler initialized with API")
            else:
                self.log_test("EventCreationHandler.__init__()", False, "Handler initialization failed")
            
            # Test step determination
            from interactive_events import InteractiveSession
            test_session = InteractiveSession("test_user", "event")
            
            # Empty session should start with 'title'
            current_step = handler.get_current_step(test_session)
            if current_step == 'title':
                self.log_test("EventCreationHandler.get_current_step() - empty", True, "Correct first step")
            else:
                self.log_test("EventCreationHandler.get_current_step() - empty", False, f"Wrong first step: {current_step}")
            
            # Add some data and test progression
            test_session.data['title'] = "Test Event"
            current_step = handler.get_current_step(test_session)
            if current_step == 'description':
                self.log_test("EventCreationHandler.get_current_step() - with title", True, "Correct next step")
            else:
                self.log_test("EventCreationHandler.get_current_step() - with title", False, f"Wrong next step: {current_step}")
                
        except Exception as e:
            self.log_test("Event Handlers", False, f"Error testing event handlers: {str(e)}")

    def test_tournament_handlers(self):
        """Test tournament creation handlers"""
        print("\n" + "="*60)
        print("TESTING TOURNAMENT HANDLERS")
        print("="*60)
        
        try:
            from tournament_handlers import TournamentCreationHandler
            from verselink_api import VerselinkAPI
            
            # Test TournamentCreationHandler creation
            api = VerselinkAPI()
            handler = TournamentCreationHandler(api)
            
            if hasattr(handler, 'api') and handler.api == api:
                self.log_test("TournamentCreationHandler.__init__()", True, "Handler initialized with API")
            else:
                self.log_test("TournamentCreationHandler.__init__()", False, "Handler initialization failed")
            
            # Test step determination
            from interactive_events import InteractiveSession
            test_session = InteractiveSession("test_user", "tournament")
            
            # Empty session should start with 'name'
            current_step = handler.get_current_step(test_session)
            if current_step == 'name':
                self.log_test("TournamentCreationHandler.get_current_step() - empty", True, "Correct first step")
            else:
                self.log_test("TournamentCreationHandler.get_current_step() - empty", False, f"Wrong first step: {current_step}")
            
            # Test date parsing functionality
            try:
                from datetime import datetime
                parsed_date = handler.parse_date("25/12/2025 20:30")
                if isinstance(parsed_date, datetime):
                    self.log_test("TournamentCreationHandler.parse_date() - standard", True, f"Parsed: {parsed_date}")
                else:
                    self.log_test("TournamentCreationHandler.parse_date() - standard", False, "Date parsing failed")
            except Exception as e:
                self.log_test("TournamentCreationHandler.parse_date() - standard", False, f"Date parsing error: {str(e)}")
                
        except Exception as e:
            self.log_test("Tournament Handlers", False, f"Error testing tournament handlers: {str(e)}")

    async def test_api_integration(self):
        """Test VerseLink API integration"""
        print("\n" + "="*60)
        print("TESTING API INTEGRATION")
        print("="*60)
        
        try:
            from verselink_api import VerselinkAPI
            
            # Test API initialization
            api = VerselinkAPI()
            
            if hasattr(api, 'base_url') and api.base_url:
                self.log_test("VerselinkAPI.__init__()", True, f"API initialized with base URL: {api.base_url}")
            else:
                self.log_test("VerselinkAPI.__init__()", False, "API initialization failed")
            
            # Test API health check (this might fail if API is not configured properly)
            try:
                async with api as api_client:
                    health_response = await api_client.get_health()
                    if isinstance(health_response, dict):
                        self.log_test("VerselinkAPI.get_health()", True, f"Health check successful: {health_response}")
                    else:
                        self.log_test("VerselinkAPI.get_health()", False, "Health check returned invalid response")
            except Exception as e:
                self.log_test("VerselinkAPI.get_health()", False, f"Health check failed: {str(e)}")
            
            # Test API methods exist
            api_methods = [
                'verify_bot', 'get_health', 'get_stats', 'register_guild', 'get_guild_config',
                'announce_event', 'announce_tournament', 'sync_message', 'schedule_reminder',
                'get_events', 'get_event', 'get_tournaments', 'get_tournament',
                'join_event', 'leave_event', 'get_organizations', 'get_organization'
            ]
            
            for method_name in api_methods:
                if hasattr(api, method_name) and callable(getattr(api, method_name)):
                    self.log_test(f"VerselinkAPI.{method_name}()", True, "Method exists and is callable")
                else:
                    self.log_test(f"VerselinkAPI.{method_name}()", False, "Method missing or not callable")
                    
        except Exception as e:
            self.log_test("API Integration", False, f"Error testing API integration: {str(e)}")

    def test_discord_ui_components(self):
        """Test Discord UI components"""
        print("\n" + "="*60)
        print("TESTING DISCORD UI COMPONENTS")
        print("="*60)
        
        try:
            from interactive_events import EventCreationView
            from interactive_events import SessionManager
            
            # Test EventCreationView creation
            session_manager = SessionManager()
            view = EventCreationView(session_manager)
            
            if hasattr(view, 'session_manager') and view.session_manager == session_manager:
                self.log_test("EventCreationView.__init__()", True, "View initialized with session manager")
            else:
                self.log_test("EventCreationView.__init__()", False, "View initialization failed")
            
            # Test that view has select component
            if hasattr(view, 'children') and len(view.children) > 0:
                self.log_test("EventCreationView.children", True, f"View has {len(view.children)} UI components")
            else:
                self.log_test("EventCreationView.children", False, "View has no UI components")
                
        except Exception as e:
            self.log_test("Discord UI Components", False, f"Error testing UI components: {str(e)}")

    def test_utility_functions(self):
        """Test utility functions"""
        print("\n" + "="*60)
        print("TESTING UTILITY FUNCTIONS")
        print("="*60)
        
        try:
            from utils import (
                create_embed, create_error_embed, create_success_embed, 
                create_warning_embed, create_info_embed, format_datetime,
                chunk_text
            )
            
            # Test embed creation
            embed = create_embed("Test Title", "Test Description")
            if hasattr(embed, 'title') and embed.title == "Test Title":
                self.log_test("create_embed()", True, "Basic embed created successfully")
            else:
                self.log_test("create_embed()", False, "Basic embed creation failed")
            
            # Test error embed
            error_embed = create_error_embed("Error Title", "Error Description")
            if hasattr(error_embed, 'color') and error_embed.color.value == 0xEF4444:
                self.log_test("create_error_embed()", True, "Error embed has correct color")
            else:
                self.log_test("create_error_embed()", False, "Error embed color incorrect")
            
            # Test success embed
            success_embed = create_success_embed("Success Title", "Success Description")
            if hasattr(success_embed, 'color') and success_embed.color.value == 0x10B981:
                self.log_test("create_success_embed()", True, "Success embed has correct color")
            else:
                self.log_test("create_success_embed()", False, "Success embed color incorrect")
            
            # Test text chunking
            long_text = "A" * 3000  # Text longer than Discord limit
            chunks = chunk_text(long_text, 2000)
            if len(chunks) > 1 and all(len(chunk) <= 2000 for chunk in chunks):
                self.log_test("chunk_text()", True, f"Text split into {len(chunks)} chunks")
            else:
                self.log_test("chunk_text()", False, "Text chunking failed")
            
            # Test datetime formatting
            test_datetime = "2025-01-27T20:30:00Z"
            formatted = format_datetime(test_datetime)
            if formatted.startswith("<t:") and formatted.endswith(":F>"):
                self.log_test("format_datetime()", True, f"DateTime formatted: {formatted}")
            else:
                self.log_test("format_datetime()", False, "DateTime formatting failed")
                
        except Exception as e:
            self.log_test("Utility Functions", False, f"Error testing utility functions: {str(e)}")

    def test_bot_main_class(self):
        """Test main bot class structure"""
        print("\n" + "="*60)
        print("TESTING BOT MAIN CLASS")
        print("="*60)
        
        try:
            from bot import VerselinkBot
            
            # Test bot class exists and has required methods
            required_methods = [
                'setup_hook', 'on_ready', 'on_guild_join', 'on_guild_remove',
                'on_message', 'register_all_guilds', 'on_command_error',
                'on_app_command_error', 'close'
            ]
            
            for method_name in required_methods:
                if hasattr(VerselinkBot, method_name):
                    self.log_test(f"VerselinkBot.{method_name}", True, "Method exists")
                else:
                    self.log_test(f"VerselinkBot.{method_name}", False, "Method missing")
            
            # Test bot initialization (without actually creating instance to avoid Discord connection)
            if hasattr(VerselinkBot, '__init__'):
                self.log_test("VerselinkBot.__init__", True, "Bot class can be initialized")
            else:
                self.log_test("VerselinkBot.__init__", False, "Bot class initialization missing")
                
        except Exception as e:
            self.log_test("Bot Main Class", False, f"Error testing bot class: {str(e)}")

    def test_command_structure(self):
        """Test command structure and cogs"""
        print("\n" + "="*60)
        print("TESTING COMMAND STRUCTURE")
        print("="*60)
        
        try:
            # Test InteractiveEvents cog
            from interactive_events import InteractiveEvents
            
            if hasattr(InteractiveEvents, 'create_event_interactive'):
                self.log_test("InteractiveEvents.create_event_interactive", True, "Create event command exists")
            else:
                self.log_test("InteractiveEvents.create_event_interactive", False, "Create event command missing")
            
            if hasattr(InteractiveEvents, 'create_tournament_interactive'):
                self.log_test("InteractiveEvents.create_tournament_interactive", True, "Create tournament command exists")
            else:
                self.log_test("InteractiveEvents.create_tournament_interactive", False, "Create tournament command missing")
            
            # Test EventManagement cog
            from event_management import EventManagement
            
            event_management_commands = [
                'start_event', 'cancel_event', 'edit_event', 'event_participants',
                'join_event', 'leave_event', 'my_events'
            ]
            
            for command_name in event_management_commands:
                if hasattr(EventManagement, command_name):
                    self.log_test(f"EventManagement.{command_name}", True, "Command exists")
                else:
                    self.log_test(f"EventManagement.{command_name}", False, "Command missing")
                    
        except Exception as e:
            self.log_test("Command Structure", False, f"Error testing command structure: {str(e)}")

    def test_phase2_features(self):
        """Test Phase 2 specific features"""
        print("\n" + "="*60)
        print("TESTING PHASE 2 SPECIFIC FEATURES")
        print("="*60)
        
        # Test event types support
        try:
            from interactive_events import EventCreationView
            from interactive_events import SessionManager
            
            session_manager = SessionManager()
            view = EventCreationView(session_manager)
            
            # Check if view has the expected event type options
            if hasattr(view, 'children') and len(view.children) > 0:
                select_component = view.children[0]
                if hasattr(select_component, 'options'):
                    event_types = [option.value for option in select_component.options]
                    expected_types = ['raid', 'course', 'pvp', 'fps', 'salvaging', 'logistique', 
                                    'exploration', 'mining', 'trading', 'roleplay', 'autre']
                    
                    if all(event_type in event_types for event_type in expected_types):
                        self.log_test("Event Types Support", True, f"All {len(expected_types)} event types supported")
                    else:
                        missing = [t for t in expected_types if t not in event_types]
                        self.log_test("Event Types Support", False, f"Missing event types: {missing}")
                else:
                    self.log_test("Event Types Support", False, "Select component has no options")
            else:
                self.log_test("Event Types Support", False, "View has no select component")
                
        except Exception as e:
            self.log_test("Phase 2 Features", False, f"Error testing Phase 2 features: {str(e)}")

    def test_session_timeout_logic(self):
        """Test session timeout and cleanup logic"""
        print("\n" + "="*60)
        print("TESTING SESSION TIMEOUT LOGIC")
        print("="*60)
        
        try:
            from interactive_events import InteractiveSession, SessionManager
            from datetime import datetime, timedelta
            
            # Test session expiration
            session = InteractiveSession("test_user", "event")
            
            # Manually set old timestamp to test expiration
            session.last_activity = datetime.utcnow() - timedelta(minutes=35)
            
            if session.is_expired(30):  # 30 minute timeout
                self.log_test("InteractiveSession.is_expired()", True, "Session correctly identified as expired")
            else:
                self.log_test("InteractiveSession.is_expired()", False, "Session expiration logic failed")
            
            # Test session manager cleanup
            manager = SessionManager()
            expired_session = manager.create_session("expired_user", "event")
            expired_session.last_activity = datetime.utcnow() - timedelta(minutes=35)
            
            manager.cleanup_expired()
            
            # Try to get the expired session
            retrieved = manager.get_session("expired_user")
            if retrieved is None:
                self.log_test("SessionManager.cleanup_expired()", True, "Expired sessions cleaned up")
            else:
                self.log_test("SessionManager.cleanup_expired()", False, "Expired sessions not cleaned up")
                
        except Exception as e:
            self.log_test("Session Timeout Logic", False, f"Error testing timeout logic: {str(e)}")

    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting VerseLink Discord Bot Phase 2 Tests")
        print("="*80)
        
        # Run synchronous tests
        self.test_module_imports()
        self.test_configuration_validation()
        self.test_interactive_session_classes()
        self.test_event_handlers()
        self.test_tournament_handlers()
        self.test_discord_ui_components()
        self.test_utility_functions()
        self.test_bot_main_class()
        self.test_command_structure()
        self.test_phase2_features()
        self.test_session_timeout_logic()
        
        # Run async tests
        await self.test_api_integration()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
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
    tester = DiscordBotPhase2Tester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())