import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord Bot Configuration
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # VerseLink API Configuration
    VERSELINK_API_BASE = os.getenv('VERSELINK_API_BASE', 'http://89.88.206.99:8001/api/v1')
    VERSELINK_API_TOKEN = os.getenv('VERSELINK_API_TOKEN')
    
    # Bot Configuration
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!vl')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
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