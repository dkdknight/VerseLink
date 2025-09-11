#!/usr/bin/env python3
"""
Direct test of Discord Events Service without FastAPI server
"""

import asyncio
import sys
import os
sys.path.append('/app/backend')

async def test_discord_events_service():
    """Test Discord Events Service directly"""
    
    print("🎮 Testing Discord Events Service Directly")
    print("=" * 50)
    
    try:
        # Test 1: Import Discord Events Service
        print("\n📦 Test 1: Import Discord Events Service...")
        from services.discord_events_service import DiscordEventsService
        print("✅ DiscordEventsService imported successfully")
        
        # Test 2: Initialize service
        print("\n🔧 Test 2: Initialize Discord Events Service...")
        service = DiscordEventsService()
        print("✅ DiscordEventsService initialized successfully")
        
        # Test 3: Check if bot token is configured
        print("\n🔑 Test 3: Check Discord Bot Token Configuration...")
        if service.bot_token and service.bot_token != "your-discord-bot-token":
            print("✅ Discord bot token is configured")
        else:
            print("⚠️ Discord bot token not configured (expected for testing)")
        
        # Test 4: Test database connection
        print("\n🗄️ Test 4: Test Database Connection...")
        from database import init_db, get_database
        await init_db()
        db = get_database()
        await db.client.admin.command('ping')
        print("✅ Database connection successful")
        
        # Test 5: Test Discord Events Router Import
        print("\n📋 Test 5: Import Discord Events Router...")
        from routers.discord_events import router
        print("✅ Discord Events Router imported successfully")
        
        # Test 6: Test Discord Integration Models
        print("\n📊 Test 6: Import Discord Integration Models...")
        from models.discord_integration import (
            DiscordEvent, DiscordEventCreate, InteractiveMessage,
            DiscordJob, DiscordJobCreate, JobType, JobStatus
        )
        print("✅ Discord Integration Models imported successfully")
        
        # Test 7: Test model creation
        print("\n🏗️ Test 7: Test Model Creation...")
        from datetime import datetime, timedelta
        
        # Test DiscordEventCreate model
        event_data = {
            "name": "Test Discord Event",
            "description": "Test event for Discord integration",
            "scheduled_start_time": datetime.utcnow() + timedelta(hours=1),
            "guild_id": "123456789012345678",
            "verselink_event_id": "test-event-123"
        }
        
        discord_event_create = DiscordEventCreate(**event_data)
        print("✅ DiscordEventCreate model created successfully")
        
        # Test DiscordJobCreate model
        job_data = {
            "job_type": JobType.CREATE_DISCORD_EVENT,
            "guild_id": "123456789012345678",
            "event_id": "test-event-123",
            "payload": {
                "event_id": "test-event-123",
                "create_channels": True,
                "create_signup_message": True
            }
        }
        
        discord_job_create = DiscordJobCreate(**job_data)
        print("✅ DiscordJobCreate model created successfully")
        
        print("\n" + "=" * 50)
        print("🎉 ALL DISCORD EVENTS SERVICE TESTS PASSED!")
        print("✨ Discord Events integration is ready for testing")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_discord_events_service())
    if result:
        print("\n🚀 Discord Events Service is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 Discord Events Service has issues")
        sys.exit(1)