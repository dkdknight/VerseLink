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
    
    # Notifications indexes
    await database.notifications.create_index("user_id")
    await database.notifications.create_index([("user_id", 1), ("read_at", 1)])
    await database.notifications.create_index("created_at")
    await database.notifications.create_index("expires_at", sparse=True)
    await database.notifications.create_index("type")
    await database.notifications.create_index("priority")
    
    # Notification preferences indexes
    await database.notification_preferences.create_index([("user_id", 1), ("notification_type", 1)], unique=True)
    await database.notification_preferences.create_index("user_id")
    
    # Reports indexes
    await database.reports.create_index("reported_user_id")
    await database.reports.create_index("reporter_user_id")
    await database.reports.create_index("status")
    await database.reports.create_index("created_at")
    await database.reports.create_index([("reporter_user_id", 1), ("reported_user_id", 1), ("created_at", 1)])
    
    # Audit logs indexes
    await database.audit_logs.create_index("actor_user_id")
    await database.audit_logs.create_index("target_user_id")
    await database.audit_logs.create_index("action")
    await database.audit_logs.create_index("created_at")
    await database.audit_logs.create_index([("target_user_id", 1), ("action", 1)])
    
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
    
    # Discord integration indexes (Phase 5)
    await database.discord_guilds.create_index("guild_id", unique=True)
    await database.discord_guilds.create_index("org_id", sparse=True)
    await database.discord_guilds.create_index("owner_id")
    await database.discord_guilds.create_index("status")
    await database.discord_guilds.create_index("api_key", unique=True)
    
    # Discord events indexes
    await database.discord_events.create_index([("guild_id", 1), ("verselink_event_id", 1)], unique=True)
    await database.discord_events.create_index("discord_event_id", unique=True)
    await database.discord_events.create_index("verselink_event_id")
    await database.discord_events.create_index("status")
    await database.discord_events.create_index("scheduled_start_time")
    await database.discord_events.create_index("created_at")
    
    # Interactive messages indexes
    await database.interactive_messages.create_index("guild_id")
    await database.interactive_messages.create_index("verselink_event_id")
    await database.interactive_messages.create_index("discord_message_id", unique=True, sparse=True)
    await database.interactive_messages.create_index("active")
    await database.interactive_messages.create_index("created_at")
    
    # Discord role mappings indexes  
    await database.discord_role_mappings.create_index([("guild_id", 1), ("discord_role_id", 1)], unique=True)
    await database.discord_role_mappings.create_index("verselink_entity_id")
    await database.discord_role_mappings.create_index("verselink_role_type")
    await database.discord_role_mappings.create_index("auto_assign")
    
    # Discord channel mappings indexes
    await database.discord_channel_mappings.create_index([("guild_id", 1), ("discord_channel_id", 1)], unique=True)
    await database.discord_channel_mappings.create_index("verselink_event_id")
    await database.discord_channel_mappings.create_index("auto_created")
    await database.discord_channel_mappings.create_index("created_at")
    
    # Discord jobs indexes
    await database.discord_jobs.create_index("status")
    await database.discord_jobs.create_index("scheduled_at")
    await database.discord_jobs.create_index("guild_id")
    await database.discord_jobs.create_index("job_type")
    await database.discord_jobs.create_index([("status", 1), ("scheduled_at", 1)])
    await database.discord_jobs.create_index("created_at")
    
    # Webhook logs indexes
    await database.webhook_logs.create_index("guild_id")
    await database.webhook_logs.create_index("webhook_type")
    await database.webhook_logs.create_index("event_type")
    await database.webhook_logs.create_index("created_at")
    await database.webhook_logs.create_index("processed")
    await database.webhook_logs.create_index([("processed", 1), ("retry_count", 1)])
    
    # Synced messages indexes
    await database.synced_messages.create_index("original_guild_id")
    await database.synced_messages.create_index([("original_guild_id", 1), ("original_message_id", 1)], unique=True)
    await database.synced_messages.create_index("created_at")
    
    # Reminder configs indexes
    await database.reminder_configs.create_index("guild_id")
    await database.reminder_configs.create_index([("guild_id", 1), ("reminder_type", 1)], unique=True)

    # Chat messages indexes
    await database.chat_messages.create_index([("context", 1), ("context_id", 1), ("created_at", 1)])
    
    # Discord guilds indexes
    try:
        await database.discord_guilds.create_index("guild_id", unique=True)
    except:
        pass  # Index might already exist
        
    try:
        await database.discord_guilds.create_index("org_id", name="discord_guild_org_id")
    except:
        pass  # Index might already exist
        
    try:
        await database.discord_guilds.create_index("status", name="discord_guild_status")
    except:
        pass  # Index might already exist
    
    # Notifications indexes
    await database.notifications.create_index("user_id")
    await database.notifications.create_index("created_at")
    
    # Auto-moderation indexes
    await database.user_messages.create_index("user_id")
    await database.user_messages.create_index("created_at")
    await database.auto_moderation_logs.create_index("user_id")
    await database.auto_moderation_logs.create_index("created_at")
    await database.notification_preferences.create_index("user_id")
    await database.notification_preferences.create_index([("user_id", 1), ("notification_type", 1)], unique=True)
    
    logger.info("All database indexes created successfully")

def get_database():
    return database