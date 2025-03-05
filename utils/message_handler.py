import discord
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import ChatView
from database import save_message, get_active_chat, end_chat, get_chat_details, get_request_by_chat_id, get_request_by_id

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
        # Include both display name and username in the author field
        embed.set_author(name=f"{message.author.display_name} ({message.author.name})", icon_url=message.author.display_avatar.url)
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
    
    async def end_user_chat(self, user_id, silent=False):
        """End a chat for a user and notify their partner."""
        chat_data = self.active_chats.pop(user_id, None)
        if not chat_data:
            return False
        
        partner_id = chat_data['partner_id']
        chat_id = chat_data['chat_id']
        
        # Calculate duration in minutes
        duration = int((datetime.now() - chat_data['start_time']).total_seconds() / 60)
        
        # End chat in database
        await end_chat(chat_id, duration)
        
        # Update the original request message with completion details
        await self.update_request_message(chat_id)
        
        if not silent:
            # Notify both users about the chat ending
            user = await self.bot.fetch_user(user_id)
            partner = await self.bot.fetch_user(partner_id)
            
            # Create stylized end chat embeds
            user_name = f"{user.display_name} ({user.name})"
            partner_name = f"{partner.display_name} ({partner.name})"
            
            user_embed = discord.Embed(
                title="☕ Coffee Chat Ended",
                description=f"Your coffee chat with **{partner_name}** has ended.",
                color=discord.Color.purple()
            )
            user_embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            user_embed.add_field(name="Ended at", value=f"<t:{int(datetime.now().timestamp())}:f>", inline=True)
            user_embed.set_footer(text=f"Chat ID: {chat_id}")
            
            partner_embed = discord.Embed(
                title="☕ Coffee Chat Ended",
                description=f"Your coffee chat with **{user_name}** has ended.",
                color=discord.Color.purple()
            )
            partner_embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            partner_embed.add_field(name="Ended at", value=f"<t:{int(datetime.now().timestamp())}:f>", inline=True)
            partner_embed.set_footer(text=f"Chat ID: {chat_id}")
            
            # Notify users with stylized embeds
            await user.send(embed=user_embed)
            await partner.send(embed=partner_embed)
        
        # Clean up active chats
        await self.cleanup_chat(partner_id)
        
        # Update bot status after ending a chat
        await self.update_bot_status()
        
        logger.info(f"Ended chat {chat_id} between users {user_id} and {partner_id}")
        return True
        
    async def update_bot_status(self):
        """Update the bot's status to reflect available coffee chats."""
        if hasattr(self.bot, 'status_updater') and self.bot.status_updater:
            await self.bot.status_updater.update_status()
    
    async def update_request_message(self, chat_id=None, request_id=None):
        """Update a request message with the latest status."""
        if not chat_id and not request_id:
            return False
        
        try:
            if chat_id:
                # Get request by chat_id
                request = await get_request_by_chat_id(chat_id)
            else:
                # Get request by request_id
                request = await get_request_by_id(request_id)
            
            if not request:
                return False
            
            # Get message details
            guild_id = request['guild_id']
            channel_id = request['channel_id']
            message_id = request['message_id']
            
            # Get guild and channel
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return False
            
            channel = guild.get_channel(channel_id)
            if not channel:
                return False
            
            # Try to get the message
            try:
                message = await channel.fetch_message(message_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return False
            
            # Get user information
            requester = await self.bot.fetch_user(request['requester_id'])
            requester_name = f"{requester.display_name} ({requester.name})"
            
            responder_name = "None"
            if request['responder_id']:
                responder = await self.bot.fetch_user(request['responder_id'])
                responder_name = f"{responder.display_name} ({responder.name})"
            
            # Helper function to convert timestamp string to unix timestamp
            def get_timestamp(ts):
                if not ts:
                    return int(datetime.now().timestamp())
                if isinstance(ts, str):
                    try:
                        # Try parsing ISO format
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        return int(dt.timestamp())
                    except ValueError:
                        # Default to current time if parsing fails
                        return int(datetime.now().timestamp())
                return int(ts)
            
            # Create embed based on request status
            if request['status'] == 'pending':
                embed = discord.Embed(
                    title=f"☕ Coffee Chat Request: {request['topic']}",
                    description=request['description'],
                    color=discord.Color.blue()
                )
                embed.add_field(name="Requested by", value=requester_name, inline=True)
                embed.add_field(name="Status", value="Pending", inline=True)
                embed.add_field(name="Created at", value=f"<t:{get_timestamp(request['created_at'])}:f>", inline=True)
                
                # Create view with accept button
                view = discord.ui.View()
                accept_button = discord.ui.Button(
                    label="Accept Request", 
                    style=discord.ButtonStyle.green,
                    custom_id=f"accept_request:{request['request_id']}"
                )
                view.add_item(accept_button)
                
                await message.edit(embed=embed, view=view)
                
            elif request['status'] == 'accepted':
                embed = discord.Embed(
                    title=f"☕ Coffee Chat Request: {request['topic']}",
                    description=request['description'],
                    color=discord.Color.green()
                )
                embed.add_field(name="Requested by", value=requester_name, inline=True)
                embed.add_field(name="Accepted by", value=responder_name, inline=True)
                embed.add_field(name="Status", value="In Progress", inline=True)
                embed.add_field(name="Created at", value=f"<t:{get_timestamp(request['created_at'])}:f>", inline=True)
                embed.add_field(name="Accepted at", value=f"<t:{get_timestamp(request['accepted_at'])}:f>", inline=True)
                
                await message.edit(embed=embed, view=None)
                
            elif request['status'] == 'completed':
                # Calculate duration in minutes
                duration = request['duration'] or 0
                
                embed = discord.Embed(
                    title=f"☕ Coffee Chat Request: {request['topic']}",
                    description=request['description'],
                    color=discord.Color.purple()
                )
                embed.add_field(name="Requested by", value=requester_name, inline=True)
                embed.add_field(name="Accepted by", value=responder_name, inline=True)
                embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
                embed.add_field(name="Status", value="Completed", inline=True)
                embed.add_field(name="Created at", value=f"<t:{get_timestamp(request['created_at'])}:f>", inline=True)
                embed.add_field(name="Completed at", value=f"<t:{get_timestamp(request['completed_at'])}:f>", inline=True)
                
                await message.edit(embed=embed, view=None)
                
            elif request['status'] == 'cancelled':
                embed = discord.Embed(
                    title=f"☕ Coffee Chat Request: {request['topic']}",
                    description=request['description'],
                    color=discord.Color.red()
                )
                embed.add_field(name="Requested by", value=requester_name, inline=True)
                embed.add_field(name="Status", value="Cancelled", inline=True)
                embed.add_field(name="Created at", value=f"<t:{get_timestamp(request['created_at'])}:f>", inline=True)
                embed.add_field(name="Cancelled at", value=f"<t:{get_timestamp(request['cancelled_at'])}:f>", inline=True)
                
                await message.edit(embed=embed, view=None)
            
            return True
        except Exception as e:
            logger.error(f"Error updating request message: {e}")
            return False
    
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
