import motor.motor_asyncio
from decouple import config
import logging

logger = logging.getLogger(__name__)

MONGO_URL = config("MONGO_URL", default="mongodb://localhost:27017/verselink")

# MongoDB client
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
database = client.get_database()

async def init_db():
    """Initialize database collections and indexes"""
    try:
        # Test connection
        await client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {MONGO_URL}")
        
        # Create indexes
        await create_indexes()
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def create_indexes():
    """Create database indexes for performance"""
    
    # Users collection indexes
    await database.users.create_index("discord_id", unique=True)
    await database.users.create_index("handle", unique=True)
    await database.users.create_index("email", sparse=True)
    
    # Organizations collection indexes
    await database.organizations.create_index("name", unique=True)
    await database.organizations.create_index("tag", unique=True)
    await database.organizations.create_index("discord_guild_id", sparse=True, unique=True)
    await database.organizations.create_index("owner_id")
    
    # Events collection indexes
    await database.events.create_index("slug", unique=True)
    await database.events.create_index("org_id")
    await database.events.create_index("start_at_utc")
    await database.events.create_index("type")
    await database.events.create_index("visibility")
    await database.events.create_index("state")
    await database.events.create_index("created_by")
    await database.events.create_index([("start_at_utc", 1), ("type", 1)])
    await database.events.create_index([("org_id", 1), ("state", 1)])
    
    # Event roles indexes
    await database.event_roles.create_index("event_id")
    await database.event_roles.create_index([("event_id", 1), ("name", 1)])
    
    # Fleet ships indexes
    await database.fleet_ships.create_index("event_id")
    
    # Tournaments indexes
    await database.tournaments.create_index("slug", unique=True)
    await database.tournaments.create_index("org_id")
    await database.tournaments.create_index("start_at_utc")
    await database.tournaments.create_index("format")
    await database.tournaments.create_index("state")
    await database.tournaments.create_index("created_by")
    await database.tournaments.create_index([("org_id", 1), ("state", 1)])
    
    # Teams indexes
    await database.teams.create_index("tournament_id")
    await database.teams.create_index("captain_user_id")
    await database.teams.create_index([("tournament_id", 1), ("name", 1)], unique=True)
    
    # Team members indexes
    await database.team_members.create_index([("team_id", 1), ("user_id", 1)], unique=True)
    await database.team_members.create_index("team_id")
    await database.team_members.create_index("user_id")
    
    # Matches indexes
    await database.matches.create_index("tournament_id")
    await database.matches.create_index([("tournament_id", 1), ("round", 1), ("bracket_position", 1)])
    await database.matches.create_index("state")
    await database.matches.create_index([("team_a_id", 1), ("team_b_id", 1)])
    
    # Attachments indexes
    await database.attachments.create_index("match_id")
    await database.attachments.create_index("user_id")
    await database.attachments.create_index("uploaded_at")
    
    # Event signups indexes
    await database.event_signups.create_index([("event_id", 1), ("user_id", 1)], unique=True)
    await database.event_signups.create_index("event_id")
    await database.event_signups.create_index("user_id")
    
    # Tournaments indexes  
    await database.tournaments.create_index("slug", unique=True)
    await database.tournaments.create_index("org_id")
    await database.tournaments.create_index("start_at_utc")
    
    # Organization members indexes
    await database.org_members.create_index([("org_id", 1), ("user_id", 1)], unique=True)
    await database.org_members.create_index("org_id")
    await database.org_members.create_index("user_id")
    
    # Subscriptions indexes
    await database.subscriptions.create_index([("subscriber_org_id", 1), ("publisher_org_id", 1)], unique=True)
    
    # Discord messages indexes
    await database.discord_messages.create_index([("owner_type", 1), ("owner_id", 1)])
    await database.discord_messages.create_index([("guild_id", 1), ("channel_id", 1), ("message_id", 1)], unique=True)
    
    # Notifications indexes
    await database.notifications.create_index("user_id")
    await database.notifications.create_index("created_at")
    
    logger.info("All database indexes created successfully")

def get_database():
    return database