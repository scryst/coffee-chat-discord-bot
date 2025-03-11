import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import sys

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Print debugging information
print(f"Current directory: {current_dir}")
print(f"Directory contents: {os.listdir(current_dir)}")
print(f"Python path: {sys.path}")

# Import local modules with absolute imports
try:
    from database.db_setup import initialize_database
    print("Successfully imported database.db_setup")
except ImportError as e:
    print(f"Error importing database: {e}")
    print(f"Attempting alternative import approach...")
    # Try a different approach if the first one fails
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("db_setup", os.path.join(current_dir, "database", "db_setup.py"))
        if spec and spec.loader:
            db_setup = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(db_setup)
            initialize_database = db_setup.initialize_database
            print("Alternative import successful")
        else:
            print(f"Could not find database/db_setup.py file")
            sys.exit(1)
    except Exception as e2:
        print(f"Alternative import failed: {e2}")
        sys.exit(1)

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
