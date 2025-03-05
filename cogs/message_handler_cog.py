import discord
from discord.ext import commands
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import MessageHandler

logger = logging.getLogger('coffee_bot.message_handler_cog')

class MessageHandlerCog(commands.Cog):
    """Cog for handling direct messages for coffee chats."""
    
    def __init__(self, bot):
        self.bot = bot
        self.bot.message_handler = MessageHandler(bot)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle direct messages for coffee chats."""
        # Ignore messages from the bot itself
        if message.author.bot:
            return
        
        # Only process direct messages
        if not isinstance(message.channel, discord.DMChannel):
            return
        
        # Process the message
        await self.bot.process_commands(message)
        
        # Check if user is in an active chat
        is_in_chat = await self.bot.message_handler.is_in_active_chat(message.author.id)
        
        if is_in_chat:
            # Relay the message to the chat partner
            await self.bot.message_handler.relay_message(message)
        else:
            # If not in a chat, send a helpful message
            if not message.content.startswith('/'):  # Ignore commands
                embed = discord.Embed(
                    title="☕ Coffee Chat Bot",
                    description="You're not in an active coffee chat. Use the `/coffee` command in a server to get started!",
                    color=discord.Color.blue()
                )
                
                await message.author.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MessageHandlerCog(bot))
