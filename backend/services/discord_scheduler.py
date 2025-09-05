import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from services.discord_service import DiscordService

logger = logging.getLogger(__name__)

class DiscordScheduler:
    """Background scheduler for Discord integration tasks"""
    
    def __init__(self, discord_service: Optional[DiscordService] = None):
        self.discord_service = discord_service or DiscordService()
        self.running = False
        self.task = None
        
    async def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Discord scheduler is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("Discord scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Discord scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Process Discord jobs every 30 seconds
                await self.discord_service.process_jobs()
                
                # Clean up old jobs and logs (once per hour)
                current_time = datetime.utcnow()
                if current_time.minute == 0:  # Top of the hour
                    await self._cleanup_old_data()
                
                # Wait before next iteration
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Discord scheduler error: {e}")
                # Wait a bit longer on error to avoid tight error loops
                await asyncio.sleep(60)
    
    async def _cleanup_old_data(self):
        """Clean up old jobs and webhook logs"""
        try:
            db = self.discord_service.db
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # Clean up completed/failed jobs older than 7 days
            result = await db.discord_jobs.delete_many({
                "status": {"$in": ["completed", "failed"]},
                "completed_at": {"$lt": cutoff_date}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old Discord jobs")
            
            # Clean up webhook logs older than 7 days
            result = await db.webhook_logs.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old webhook logs")
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Global scheduler instance
discord_scheduler = DiscordScheduler()

async def start_discord_scheduler():
    """Start the Discord scheduler"""
    await discord_scheduler.start()

async def stop_discord_scheduler():
    """Stop the Discord scheduler"""
    await discord_scheduler.stop()