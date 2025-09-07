#!/usr/bin/env python3
"""
Fix Discord Guild - Add missing api_key field
"""

import asyncio
import motor.motor_asyncio
from decouple import config
import uuid

async def fix_discord_guilds():
    """Add missing api_key field to existing Discord guilds"""
    try:
        # Connect to MongoDB
        mongo_url = config("MONGO_URL", default="mongodb://localhost:27017/verselink")
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db = client.get_default_database()
        
        print("🔧 Fixing Discord guilds...")
        
        # Find guilds without api_key field
        guilds_without_api_key = []
        async for guild in db.discord_guilds.find({"api_key": {"$exists": False}}):
            guilds_without_api_key.append(guild)
        
        print(f"📊 Found {len(guilds_without_api_key)} guilds without api_key field")
        
        # Update each guild to add api_key
        for guild in guilds_without_api_key:
            api_key = str(uuid.uuid4())
            
            await db.discord_guilds.update_one(
                {"_id": guild["_id"]},
                {"$set": {"api_key": api_key}}
            )
            
            print(f"✅ Updated guild {guild['guild_id']} with api_key: {api_key}")
        
        # Verify the fix
        print("\n🔍 Verifying fix...")
        test_guild = await db.discord_guilds.find_one({"guild_id": "123456789012345678"})
        if test_guild and "api_key" in test_guild:
            print(f"✅ Test guild now has api_key: {test_guild['api_key']}")
        else:
            print("❌ Test guild still missing api_key")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Error fixing guilds: {e}")

if __name__ == "__main__":
    asyncio.run(fix_discord_guilds())