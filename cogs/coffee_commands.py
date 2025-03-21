import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    CoffeeChatRequestModal,
    CoffeeChatView,
    RequestListView,
    create_request_embed,
    create_stats_embed,
    create_leaderboard_embed
)
from database import (
    get_or_create_user,
    get_or_create_server,
    create_chat_request,
    get_pending_requests,
    get_user_request,
    cancel_request,
    create_chat,
    get_user_stats,
    get_leaderboard,
    get_active_chat,
    end_chat,
    update_request_message_info,
    get_request_by_id,
    update_request_message_info
)

logger = logging.getLogger('coffee_bot.commands')

class CoffeeCommands(commands.Cog):
    """Commands for the Coffee Chat bot."""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("CoffeeCommands cog initialized")
    
    async def update_bot_status(self):
        """Update the bot's status to reflect available coffee chats."""
        if hasattr(self.bot, 'status_updater') and self.bot.status_updater:
            await self.bot.status_updater.update_status()
        else:
            # If status_updater isn't available through the bot, try to get it from the global scope
            try:
                from bot import status_updater
                if status_updater:
                    await status_updater.update_status()
            except (ImportError, NameError):
                logger.warning("Could not update bot status: status_updater not found")
    
    # Custom view for the coffee chat menu that adapts based on user state
    class CustomCoffeeChatMainView(CoffeeChatView):
        def __init__(self, request_callback, view_requests_callback, stats_callback, 
                    leaderboard_callback, cancel_callback, end_chat_callback,
                    has_pending_request, in_active_chat, request_count):
            super().__init__(request_callback, view_requests_callback, stats_callback, 
                            leaderboard_callback, cancel_callback, end_chat_callback)
            
            # Update the Cross-Server Requests button with count
            for item in self.children[:]:
                if isinstance(item, discord.ui.Button) and "Cross-Server Requests" in item.label:
                    self.remove_item(item)
                    break
            
            # Add updated button with count
            self.add_item(discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label=f"Cross-Server Requests ({request_count})",
                emoji="🔍",
                custom_id="view_requests",
                row=1
            ))
            
            # Handle button visibility based on user's status
            if in_active_chat:
                # If user is in a chat, replace the request button with an end chat button
                for item in self.children[:]:
                    if isinstance(item, discord.ui.Button) and item.label == "Request Coffee Chat":
                        self.remove_item(item)
                        break
                
                # Add End Chat button
                self.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="End Current Chat",
                    emoji="🛑",
                    custom_id="end_chat",
                    row=0
                ))
                
                # Also remove the cancel button if it exists
                for item in self.children[:]:
                    if isinstance(item, discord.ui.Button) and item.label == "Cancel My Request":
                        self.remove_item(item)
                        break
            elif has_pending_request:
                # Remove the request button if user has a pending request
                for item in self.children[:]:
                    if isinstance(item, discord.ui.Button) and item.label == "Request Coffee Chat":
                        self.remove_item(item)
                        break
            else:
                # Remove the cancel button if user doesn't have a pending request
                for item in self.children[:]:
                    if isinstance(item, discord.ui.Button) and item.label == "Cancel My Request":
                        self.remove_item(item)
                        break
        
        # Override the view_requests_button method to handle the new button
        async def view_requests_button_callback(self, interaction):
            try:
                await interaction.response.defer(ephemeral=True)
                await self.view_requests_callback(interaction)
            except discord.errors.InteractionResponded:
                # If the interaction has already been responded to, use followup instead
                await self.view_requests_callback(interaction)
            
        # Add end_chat_button callback
        async def end_chat_button_callback(self, interaction):
            try:
                await interaction.response.defer(ephemeral=True)
                await self.end_chat_callback(interaction)
            except discord.errors.InteractionResponded:
                # If the interaction has already been responded to, use followup instead
                await self.end_chat_callback(interaction)
    
    @app_commands.command(
        name="coffee", 
        description="Connect with others for cross-server coffee chats on various topics"
    )
    async def coffee(self, interaction: discord.Interaction):
        """Main command to open the Coffee Chat menu."""
        # Create or get user in database
        await get_or_create_user(
            user_id=interaction.user.id,
            username=interaction.user.name,
            discriminator=interaction.user.discriminator if hasattr(interaction.user, 'discriminator') else None
        )
        
        # Create or get server in database if in a guild
        if interaction.guild:
            await get_or_create_server(
                server_id=interaction.guild.id,
                server_name=interaction.guild.name
            )
        
        # Check if user has a pending request
        existing_request = await get_user_request(interaction.user.id)
        
        # Check if user is in an active chat
        in_active_chat = await self.bot.message_handler.is_in_active_chat(interaction.user.id)
        
        # Get the count of pending requests for the button label
        pending_requests = await get_pending_requests(exclude_user_id=interaction.user.id)
        request_count = len(pending_requests)
        
        # Create main menu view with conditional buttons
        view = self.CustomCoffeeChatMainView(
            request_callback=self.handle_request,
            view_requests_callback=self.handle_view_requests,
            stats_callback=self.handle_stats,
            leaderboard_callback=self.handle_leaderboard,
            cancel_callback=self.handle_cancel,
            end_chat_callback=self.handle_end_chat_button,
            has_pending_request=existing_request is not None,
            in_active_chat=in_active_chat,
            request_count=request_count
        )
        
        # Add callbacks for the custom buttons
        for item in view.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "view_requests":
                item.callback = view.view_requests_button_callback
            elif isinstance(item, discord.ui.Button) and item.custom_id == "end_chat":
                item.callback = view.end_chat_button_callback
        
        # Send menu
        embed = discord.Embed(
            title="☕ Coffee Chat Menu",
            description="Connect with users across different Discord servers for meaningful conversations!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="What is Coffee Chat?",
            value="Coffee Chat is a cross-server networking tool that connects you with other users for one-on-one conversations about topics you're interested in.",
            inline=False
        )
        
        embed.add_field(
            name="How it works",
            value="1. Create a request with a topic you'd like to discuss\n"
                  "2. Users from any server with this bot can see and accept your request\n"
                  "3. Chat privately through DMs with the bot acting as a relay\n"
                  "4. End the chat when you're done and earn points on the leaderboard",
            inline=False
        )
        
        if existing_request:
            embed.add_field(
                name="Your Active Request",
                value=f"Topic: **{existing_request['topic']}**\n"
                      f"Created: <t:{int(datetime.fromisoformat(existing_request['created_at']).timestamp())}:R>",
                inline=False
            )
        
        embed.set_footer(text="Coffee Chat Bot | Connect across communities")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def handle_request(self, interaction: discord.Interaction):
        """Handle a user clicking the Request Coffee Chat button."""
        # Check if user already has a pending request
        existing_request = await get_user_request(interaction.user.id)
        if existing_request:
            embed = discord.Embed(
                title="Request Already Exists",
                description="You already have a pending coffee chat request. Please cancel it before creating a new one.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed)
            return
        
        # Check if user is in a guild
        if not interaction.guild:
            embed = discord.Embed(
                title="Must be in a Server",
                description="You must be in a server to create a coffee chat request.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed)
            return
        
        # Check if user is already in a chat
        in_chat = await self.bot.message_handler.is_in_active_chat(interaction.user.id)
        if in_chat:
            embed = discord.Embed(
                title="Already in a Chat",
                description="You are already in an active coffee chat. Please finish your current chat before creating a new request.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed)
            return
        
        # Show request modal
        modal = CoffeeChatRequestModal(self.handle_request_submit)
        await interaction.response.send_modal(modal)
    
    async def handle_request_submit(self, interaction: discord.Interaction, topic, description):
        """Handle a user submitting the coffee chat request modal."""
        # Create request in database
        request = await create_chat_request(
            user_id=interaction.user.id,
            server_id=interaction.guild.id,
            topic=topic,
            description=description
        )
        
        # Create embed for request
        embed = create_request_embed(request, interaction.user)
        
        # Create view with accept button
        class AcceptRequestView(discord.ui.View):
            def __init__(self, accept_callback, bot):
                super().__init__(timeout=None)  # No timeout for request buttons
                self.accept_callback = accept_callback
                self.bot = bot
                
            @discord.ui.button(label="Accept Request", style=discord.ButtonStyle.success, emoji="✅", custom_id=f"accept_request_{request['request_id']}")
            async def accept_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                # Check if the user is the requester
                if button_interaction.user.id == request['user_id']:
                    await button_interaction.response.send_message(
                        "You cannot accept your own coffee chat request.",
                        ephemeral=True
                    )
                    return
                
                # Check if the user is already in a chat
                user_in_chat = await self.bot.message_handler.is_in_active_chat(button_interaction.user.id)
                
                if user_in_chat:
                    # Just inform the user they're already in a chat
                    await button_interaction.response.send_message(
                        "You are already in an active coffee chat. Please finish your current chat before accepting a new one.",
                        ephemeral=True
                    )
                    return
                
                # If not in a chat, proceed with the callback
                await self.accept_callback(button_interaction, request['request_id'])
        
        view = AcceptRequestView(self.handle_accept_request, self.bot)
        
        # First acknowledge the interaction
        await interaction.response.defer(ephemeral=True)
        
        # Send request to channel
        channel = interaction.channel
        request_message = await channel.send(
            f"**{interaction.user.display_name}** is looking for a coffee chat!",
            embed=embed,
            view=view
        )
        
        # Save the message ID and channel ID for future reference
        await update_request_message_info(request['request_id'], request_message.id, channel.id)
        
        # Update bot status to reflect the new request
        await self.update_bot_status()
    
    async def handle_view_requests(self, interaction: discord.Interaction):
        """Handle a user clicking the View Requests button."""
        # Get pending requests excluding the user's own
        requests = await get_pending_requests(exclude_user_id=interaction.user.id)
        
        if not requests:
            # Edit the original message instead of sending a new one
            embed = discord.Embed(
                title="No Coffee Chat Requests",
                description="There are no pending coffee chat requests at the moment. Why not create one?",
                color=discord.Color.blue()
            )
            try:
                await interaction.response.edit_message(embed=embed)
            except discord.errors.InteractionResponded:
                await interaction.followup.edit_message(interaction.message.id, embed=embed)
            return
        
        # Create embed with request info
        embed = discord.Embed(
            title=f"Coffee Chat Requests ({len(requests)})",
            description="Select a request to accept:",
            color=discord.Color.blue()
        )
        
        # Create view with request select menu
        view = RequestListView(requests, self.handle_accept_request)
        
        # Edit the original message
        try:
            await interaction.response.edit_message(embed=embed, view=view)
        except discord.errors.InteractionResponded:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)
    
    async def handle_accept_request(self, interaction: discord.Interaction, request_id):
        """Handle a user accepting a coffee chat request."""
        # Immediately defer the response to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Get the request details
        request = await get_request_by_id(request_id)
        if not request:
            await interaction.followup.send("This request is no longer available.", ephemeral=True)
            return
        
        # Check if user is trying to accept their own request
        if request['user_id'] == interaction.user.id:
            await interaction.followup.send("You cannot accept your own request.", ephemeral=True)
            return
        
        # Check if user is already in a chat
        if await self.bot.message_handler.is_in_active_chat(interaction.user.id):
            await interaction.followup.send(
                "You are already in an active coffee chat. Please end your current chat before accepting a new one.",
                ephemeral=True
            )
            return
        
        # Check if request is still pending
        if request['status'] != 'pending':
            await interaction.followup.send(
                f"This request has already been {request['status']}.",
                ephemeral=True
            )
            return
        
        # Cancel any pending requests from the accepting user
        existing_request = await get_user_request(interaction.user.id)
        if existing_request:
            await cancel_request(existing_request['request_id'])
            
            # Try to update the request message if it exists
            try:
                request_channel = self.bot.get_channel(int(existing_request['channel_id']))
                if request_channel:
                    try:
                        request_message = await request_channel.fetch_message(int(existing_request['message_id']))
                        if request_message:
                            cancelled_embed = discord.Embed(
                                title="☕ Coffee Chat Request Cancelled",
                                description=f"This request was automatically cancelled because {interaction.user.mention} accepted another coffee chat.",
                                color=discord.Color.light_grey()
                            )
                            await request_message.edit(embed=cancelled_embed, view=None)
                    except (discord.NotFound, discord.Forbidden):
                        pass  # Message may have been deleted or bot lacks permissions
            except Exception as e:
                logger.error(f"Error updating cancelled request message: {e}")
        
        # Create the chat
        requester_id = int(request['user_id'])
        accepter_id = interaction.user.id
        
        chat_id = await create_chat(request_id, requester_id, accepter_id)
        
        # Update the request status
        await update_request_message_info(request_id, 'status', 'accepted')
        
        # Get user objects
        requester = self.bot.get_user(requester_id)
        accepter = self.bot.get_user(accepter_id)
        
        if not requester or not accepter:
            # Try to fetch users if not in cache
            try:
                if not requester:
                    requester = await self.bot.fetch_user(requester_id)
                if not accepter:
                    accepter = await self.bot.fetch_user(accepter_id)
            except discord.NotFound:
                await interaction.followup.send(
                    "Could not find one of the users for this chat. The request may be invalid.",
                    ephemeral=True
                )
                return
        
        # Start the chat
        success = await self.bot.message_handler.start_chat(chat_id, requester, accepter, request['topic'])
        
        if success:
            # Send confirmation to the accepter
            await interaction.followup.send(
                f"You've accepted a coffee chat with {requester.name}! Check your DMs to start chatting.",
                ephemeral=True
            )
            
            # Update the request message
            try:
                request_channel = self.bot.get_channel(int(request['channel_id']))
                if request_channel:
                    try:
                        request_message = await request_channel.fetch_message(int(request['message_id']))
                        if request_message:
                            accepted_embed = discord.Embed(
                                title="☕ Coffee Chat In Progress",
                                description=f"**Topic:** {request['topic']}\n\n"
                                           f"**Requested by:** {requester.mention}\n"
                                           f"**Accepted by:** {accepter.mention}\n"
                                           f"**Started:** <t:{int(datetime.now().timestamp())}:R>",
                                color=discord.Color.green()
                            )
                            await request_message.edit(embed=accepted_embed, view=None)
                    except (discord.NotFound, discord.Forbidden):
                        pass  # Message may have been deleted or bot lacks permissions
            except Exception as e:
                logger.error(f"Error updating accepted request message: {e}")
            
            # Update bot status
            await self.update_bot_status()
        else:
            await interaction.followup.send(
                "There was an error starting the coffee chat. Please try again later.",
                ephemeral=True
            )
    
    async def handle_stats(self, interaction: discord.Interaction):
        """Handle a user clicking the My Stats button."""
        # Get user stats
        stats = await get_user_stats(interaction.user.id)
        
        if not stats:
            # Create default stats if none found
            stats = {
                'total_chats': 0,
                'total_time': 0,
                'rating': 0
            }
        
        # Create stats embed
        embed = create_stats_embed(interaction.user, stats)
        
        # Edit the original message
        await interaction.response.edit_message(embed=embed)
    
    async def handle_leaderboard(self, interaction: discord.Interaction):
        """Handle a user clicking the Leaderboard button."""
        # Get leaderboard data
        leaderboard = await get_leaderboard(limit=10)
        
        # Create leaderboard embed
        embed = create_leaderboard_embed(leaderboard)
        
        # Edit the original message
        await interaction.response.edit_message(embed=embed)
    
    async def handle_cancel(self, interaction: discord.Interaction):
        """Handle a user clicking the Cancel My Request button."""
        # Get user's pending request
        request = await get_user_request(interaction.user.id)
        
        if not request:
            embed = discord.Embed(
                title="No Active Request",
                description="You don't have an active coffee chat request to cancel.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed)
            return
        
        # Check if user is in an active chat
        in_active_chat = await self.bot.message_handler.is_in_active_chat(interaction.user.id)
        if in_active_chat:
            embed = discord.Embed(
                title="Cannot Cancel Request",
                description="You are currently in an active coffee chat. Please end the chat before cancelling your request.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed)
            return
        
        # Cancel the request
        await cancel_request(request['request_id'])
        
        # Update bot status
        await self.update_bot_status()
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Request Cancelled",
            description=f"Your coffee chat request '{request['topic']}' has been cancelled.",
            color=discord.Color.green()
        )
        
        # Get pending requests count for the button label
        pending_requests = await get_pending_requests(exclude_user_id=interaction.user.id)
        request_count = len(pending_requests)
        
        # Create a new custom view with the updated button configuration
        view = self.CustomCoffeeChatMainView(
            request_callback=self.handle_request,
            view_requests_callback=self.handle_view_requests,
            stats_callback=self.handle_stats,
            leaderboard_callback=self.handle_leaderboard,
            cancel_callback=self.handle_cancel,
            end_chat_callback=self.handle_end_chat_button,
            has_pending_request=False,  # No longer has a pending request
            in_active_chat=in_active_chat,
            request_count=request_count
        )
        
        # Add callback for the custom button
        for item in view.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "view_requests":
                item.callback = view.view_requests_button_callback
        
        # Edit the original message
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def handle_end_chat_button(self, interaction: discord.Interaction):
        """Handle the end chat button."""
        user_id = interaction.user.id
        
        # Check if user is in an active chat
        if user_id not in self.bot.message_handler.active_chats:
            embed = discord.Embed(
                title="No Active Chat",
                description="You are not currently in an active coffee chat.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        # Get chat partner info before ending chat
        chat_data = self.bot.message_handler.active_chats[user_id]
        partner_id = chat_data['partner_id']
        
        try:
            partner = await self.bot.fetch_user(partner_id)
            partner_name = f"{partner.display_name} ({partner.name})"
        except:
            partner_name = "your partner"
        
        # End the chat
        await self.bot.message_handler.end_user_chat(user_id)
        
        # Create stylized embed for the end chat message
        embed = discord.Embed(
            title="☕ Coffee Chat Ended",
            description=f"Your chat with **{partner_name}** has ended.",
            color=discord.Color.gold()
        )
        embed.add_field(name="Thank You", value="We hope you enjoyed your coffee chat! Feel free to start a new one anytime.", inline=False)
        
        # Create a new view with the coffee command button
        view = discord.ui.View()
        coffee_button = discord.ui.Button(
            label="Start New Coffee Chat", 
            style=discord.ButtonStyle.primary,
            custom_id="start_new_coffee"
        )
        view.add_item(coffee_button)
        
        # Update the message
        await interaction.response.edit_message(embed=embed, view=view)
    
async def setup(bot):
    await bot.add_cog(CoffeeCommands(bot))
