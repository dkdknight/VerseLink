#!/usr/bin/env python3
"""
Detailed Debug Test - Check database and endpoint issues
"""

import requests
import json
import asyncio
import motor.motor_asyncio
from decouple import config

async def check_database_connection():
    """Check if we can connect to MongoDB and see what's in the discord_guilds collection"""
    try:
        # Connect to MongoDB
        mongo_url = config("MONGO_URL", default="mongodb://localhost:27017/verselink")
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db = client.get_default_database()
        
        print("🔍 Checking MongoDB connection...")
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check discord_guilds collection
        guild_count = await db.discord_guilds.count_documents({})
        print(f"📊 Discord guilds in database: {guild_count}")
        
        if guild_count > 0:
            print("\n📋 Existing guilds:")
            async for guild in db.discord_guilds.find({}).limit(5):
                print(f"  - Guild ID: {guild.get('guild_id', 'N/A')}")
                print(f"    Name: {guild.get('guild_name', 'N/A')}")
                print(f"    API Key: {guild.get('api_key', 'N/A')}")
                print(f"    Status: {guild.get('status', 'N/A')}")
                print()
        
        # Check if the test guild exists
        test_guild = await db.discord_guilds.find_one({"guild_id": "123456789012345678"})
        if test_guild:
            print(f"🎯 Test guild found: {test_guild}")
        else:
            print("❌ Test guild (123456789012345678) not found in database")
            
            # Create a test guild
            print("🔧 Creating test guild...")
            test_guild_doc = {
                "id": "guild_123456789012345678",
                "guild_id": "123456789012345678",
                "guild_name": "Test Guild",
                "owner_id": "987654321098765432",
                "org_id": None,
                "status": "active",
                "sync_enabled": True,
                "reminder_enabled": True,
                "webhook_verified": False,
                "api_key": "test-api-key-12345",
                "created_at": "2025-01-27T10:00:00Z",
                "updated_at": "2025-01-27T10:00:00Z"
            }
            
            await db.discord_guilds.insert_one(test_guild_doc)
            print("✅ Test guild created")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def test_discord_endpoints():
    """Test Discord endpoints with detailed error reporting"""
    base_url = "https://sc-community-hub.preview.emergentagent.com"
    
    print("\n🔍 Testing Discord endpoints...")
    
    # Test 1: Guild config with query parameter
    print("\n--- Test 1: Guild Config (Query Parameter) ---")
    url = f"{base_url}/api/v1/discord/bot/guild/123456789012345678/config?api_key=test-api-key-12345"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("🚨 500 Error - This indicates a server-side issue")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 2: Guild config with different API key
    print("\n--- Test 2: Guild Config (Different API Key) ---")
    url = f"{base_url}/api/v1/discord/bot/guild/123456789012345678/config?api_key=wrong-key"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 3: Bot verify endpoint
    print("\n--- Test 3: Bot Verify ---")
    url = f"{base_url}/api/v1/discord/bot/verify"
    data = {
        "guild_id": "123456789012345678",
        "api_key": "test-api-key-12345"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Request failed: {e}")

async def main():
    """Run all tests"""
    print("🔍 DETAILED DEBUG TEST - DISCORD INTEGRATION ISSUES")
    print("="*80)
    
    await check_database_connection()
    test_discord_endpoints()

if __name__ == "__main__":
    asyncio.run(main())