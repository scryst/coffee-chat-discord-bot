import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
from database import initialize_database
from web_server import keep_alive

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

# Load cogs
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            logger.info(f'Loaded extension: {filename[:-3]}')

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')
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
