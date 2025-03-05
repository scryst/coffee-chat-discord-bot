import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import initialize_database
from web_server import keep_alive
from utils.status_updater import StatusUpdater

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('coffee_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot instance
bot = commands.Bot(command_prefix='/', intents=intents)

# Create status updater
status_updater = None

# Load cogs
async def load_extensions():
    try:
        await bot.load_extension("cogs.coffee_commands")
        logger.info(f'Loaded extension: coffee_commands')
        
        await bot.load_extension("cogs.error_handler")
        logger.info(f'Loaded extension: error_handler')
        
        await bot.load_extension("cogs.message_handler_cog")
        logger.info(f'Loaded extension: message_handler_cog')
    except Exception as e:
        logger.error(f"Failed to load extension: {e}")

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')
    
    # Initialize status updater
    global status_updater
    status_updater = StatusUpdater(bot)
    
    # Make status updater accessible to cogs
    bot.status_updater = status_updater
    
    # Initial status update
    await status_updater.update_status()
    
    # Start periodic status updates
    await status_updater.start_status_updates()
    
    # Sync commands
    await bot.tree.sync()
    logger.info('Synced application commands')

# Run the bot
async def main():
    # Initialize database
    await initialize_database()
    
    # Start the bot
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == '__main__':
    # Start web server for Replit hosting
    keep_alive()
    
    # Run the bot
    import asyncio
    asyncio.run(main())
