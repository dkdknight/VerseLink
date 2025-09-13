import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class Config:
    # Discord Bot Configuration
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # VerseLink API Configuration
    VERSELINK_API_BASE = os.getenv('VERSELINK_API_BASE', 'http://89.88.206.99:8001/api/v1')
    VERSELINK_API_TOKEN = os.getenv('VERSELINK_API_TOKEN')

     # API Retry/Backoff Configuration
    API_MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', '3'))
    API_BACKOFF_FACTOR = float(os.getenv('API_BACKOFF_FACTOR', '1'))
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))
    
    # Bot Configuration
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!vl')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    BOT_API_PORT = int(os.getenv('BOT_API_PORT', '8050'))
    BOT_API_TOKEN = os.getenv('BOT_API_TOKEN', '')
    
    # Webhook configuration
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret-change-this')
    WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8050'))
    
    # Validation
    @classmethod
    def validate(cls):
        missing = []
        if not cls.DISCORD_BOT_TOKEN:
            missing.append('DISCORD_BOT_TOKEN')
        if not cls.VERSELINK_API_TOKEN:
            missing.append('VERSELINK_API_TOKEN')
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def get_headers(cls):
        """Get headers for VerseLink API requests"""
        return {
            'Authorization': f'Bearer {cls.VERSELINK_API_TOKEN}',
            'Content-Type': 'application/json',
            'User-Agent': 'VerseLink-Discord-Bot/1.0'
            }

    @classmethod
    def get_site_base(cls) -> str:
        """Get base URL for VerseLink site from API base"""
        parsed = urlparse(cls.VERSELINK_API_BASE)
        base = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
            base += f":{parsed.port}"
        return base