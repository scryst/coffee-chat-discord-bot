import discord
import logging
from datetime import datetime
from .ui import ChatView
from ..database import save_message, get_active_chat, end_chat

logger = logging.getLogger('coffee_bot.message_handler')

class MessageHandler:
    """Handles message relaying between users in a coffee chat."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_chats = {}  # {user_id: {chat_id, partner_id, start_time}}
    
    async def start_chat(self, chat_data):
        """Start a new chat between two users."""
        chat_id = chat_data['chat_id']
        user1_id = chat_data['user1_id']
        user2_id = chat_data['user2_id']
        topic = chat_data['topic']
        
        # Setup chat data for both users
        now = datetime.now()
        self.active_chats[user1_id] = {
            'chat_id': chat_id,
            'partner_id': user2_id,
            'start_time': now
        }
        self.active_chats[user2_id] = {
            'chat_id': chat_id,
            'partner_id': user1_id,
            'start_time': now
        }
        
        # Send initial messages to both users
        user1 = await self.bot.fetch_user(user1_id)
        user2 = await self.bot.fetch_user(user2_id)
        
        # Create chat view for ending the chat
        view = ChatView(self.handle_end_chat)
        
        # Send welcome message to user1
        embed1 = discord.Embed(
            title=f"☕ Coffee Chat Started: {topic}",
            description=f"You are now chatting with **{user2.display_name}**. All messages you send here will be relayed to them.",
            color=discord.Color.green()
        )
        embed1.add_field(name="How to use", value="Simply type messages in this DM to chat. Click 'End Chat' when you're finished.")
        embed1.set_footer(text=f"Chat ID: {chat_id}")
        
        try:
            await user1.send(embed=embed1, view=view)
        except discord.Forbidden:
            logger.error(f"Cannot send DM to user {user1_id}")
            await self.cleanup_chat(user1_id)
            return False
        
        # Send welcome message to user2
        embed2 = discord.Embed(
            title=f"☕ Coffee Chat Started: {topic}",
            description=f"You are now chatting with **{user1.display_name}**. All messages you send here will be relayed to them.",
            color=discord.Color.green()
        )
        embed2.add_field(name="How to use", value="Simply type messages in this DM to chat. Click 'End Chat' when you're finished.")
        embed2.set_footer(text=f"Chat ID: {chat_id}")
        
        try:
            await user2.send(embed=embed2, view=view)
        except discord.Forbidden:
            logger.error(f"Cannot send DM to user {user2_id}")
            await self.cleanup_chat(user2_id)
            return False
        
        logger.info(f"Started chat {chat_id} between users {user1_id} and {user2_id}")
        return True
    
    async def relay_message(self, message):
        """Relay a message from one user to another in an active chat."""
        author_id = message.author.id
        
        # Check if user is in an active chat
        if author_id not in self.active_chats:
            return False
        
        chat_data = self.active_chats[author_id]
        chat_id = chat_data['chat_id']
        partner_id = chat_data['partner_id']
        
        # Get partner user
        try:
            partner = await self.bot.fetch_user(partner_id)
        except discord.NotFound:
            logger.error(f"Partner user {partner_id} not found")
            await self.end_user_chat(author_id)
            return False
        
        # Create embed for the message
        embed = discord.Embed(
            description=message.content if message.content else "*No text content*",
            color=discord.Color.blue()
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.timestamp = message.created_at
        
        # Handle attachments
        files = []
        has_attachment = False
        
        for attachment in message.attachments:
            try:
                file = await attachment.to_file()
                files.append(file)
                has_attachment = True
            except discord.HTTPException:
                logger.error(f"Failed to download attachment from {message.author.id}")
        
        # Send message to partner
        try:
            await partner.send(embed=embed, files=files)
        except discord.Forbidden:
            logger.error(f"Cannot send message to user {partner_id}")
            await self.end_user_chat(author_id)
            return False
        
        # Save message to database
        await save_message(
            chat_id=chat_id,
            sender_id=author_id,
            content=message.content,
            has_attachment=has_attachment
        )
        
        return True
    
    async def handle_end_chat(self, interaction):
        """Handle a user clicking the End Chat button."""
        user_id = interaction.user.id
        
        if user_id not in self.active_chats:
            await interaction.response.send_message("You don't have an active chat.", ephemeral=True)
            return
        
        await interaction.response.defer()
        await self.end_user_chat(user_id)
    
    async def end_user_chat(self, user_id):
        """End a chat for a user and notify their partner."""
        if user_id not in self.active_chats:
            return False
        
        chat_data = self.active_chats[user_id]
        chat_id = chat_data['chat_id']
        partner_id = chat_data['partner_id']
        start_time = chat_data['start_time']
        
        # Calculate duration in minutes
        duration = int((datetime.now() - start_time).total_seconds() / 60)
        
        # End chat in database
        await end_chat(chat_id, duration)
        
        # Notify both users
        user = await self.bot.fetch_user(user_id)
        partner = await self.bot.fetch_user(partner_id)
        
        end_embed = discord.Embed(
            title="☕ Coffee Chat Ended",
            description=f"Your coffee chat has ended. Duration: {duration} minutes.",
            color=discord.Color.red()
        )
        end_embed.set_footer(text=f"Chat ID: {chat_id}")
        
        try:
            await user.send(embed=end_embed)
        except discord.Forbidden:
            logger.error(f"Cannot send end message to user {user_id}")
        
        try:
            await partner.send(embed=end_embed)
        except discord.Forbidden:
            logger.error(f"Cannot send end message to user {partner_id}")
        
        # Clean up active chats
        await self.cleanup_chat(user_id)
        
        logger.info(f"Ended chat {chat_id} between users {user_id} and {partner_id}")
        return True
    
    async def cleanup_chat(self, user_id):
        """Clean up chat data for a user and their partner."""
        if user_id not in self.active_chats:
            return
        
        partner_id = self.active_chats[user_id]['partner_id']
        
        # Remove both users from active chats
        if user_id in self.active_chats:
            del self.active_chats[user_id]
        
        if partner_id in self.active_chats:
            del self.active_chats[partner_id]
    
    async def is_in_active_chat(self, user_id):
        """Check if a user is in an active chat."""
        # First check our local cache
        if user_id in self.active_chats:
            return True
        
        # Then check the database as a fallback
        chat = await get_active_chat(user_id)
        if chat:
            # Restore the chat data in our cache
            partner_id = chat['user1_id'] if user_id == chat['user2_id'] else chat['user2_id']
            self.active_chats[user_id] = {
                'chat_id': chat['chat_id'],
                'partner_id': partner_id,
                'start_time': datetime.now()  # Approximation since we don't know the exact start time
            }
            return True
        
        return False
