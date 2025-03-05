import discord
import logging
import asyncio
from database.db_operations import get_pending_requests

logger = logging.getLogger('coffee_bot.status_updater')

class StatusUpdater:
    """Class to manage the bot's status based on available coffee chat requests."""
    
    def __init__(self, bot):
        self.bot = bot
        self.update_interval = 300  # Update every 5 minutes by default
        self.task = None
    
    async def update_status(self):
        """Update the bot's status to show the number of available coffee chat requests."""
        try:
            # Get all pending requests
            requests = await get_pending_requests()
            request_count = len(requests)
            
            # Create appropriate status message
            if request_count == 0:
                status_text = "/coffee | No active requests"
            elif request_count == 1:
                status_text = f"/coffee | 1 coffee chat available"
            else:
                status_text = f"/coffee | {request_count} coffee chats available"
            
            # Set the bot's activity
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=status_text
            )
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            logger.info(f"Updated bot status: {status_text}")
            
        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
    
    async def start_status_updates(self):
        """Start the periodic status update task."""
        if self.task is not None:
            self.task.cancel()
        
        self.task = asyncio.create_task(self._status_update_loop())
        logger.info("Started status update task")
    
    async def _status_update_loop(self):
        """Background task to periodically update the bot's status."""
        try:
            while True:
                await self.update_status()
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            logger.info("Status update task cancelled")
        except Exception as e:
            logger.error(f"Error in status update loop: {e}")
    
    def stop_status_updates(self):
        """Stop the periodic status update task."""
        if self.task is not None:
            self.task.cancel()
            self.task = None
            logger.info("Stopped status update task")
