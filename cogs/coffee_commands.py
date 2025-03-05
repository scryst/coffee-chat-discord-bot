import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from ..utils import (
    CoffeeChatRequestModal,
    CoffeeChatMainView,
    RequestListView,
    create_request_embed,
    create_stats_embed,
    create_leaderboard_embed
)
from ..database import (
    get_or_create_user,
    get_or_create_server,
    create_chat_request,
    get_pending_requests,
    get_user_request,
    cancel_request,
    create_chat,
    get_user_stats,
    get_leaderboard
)

logger = logging.getLogger('coffee_bot.commands')

class CoffeeCommands(commands.Cog):
    """Commands for the Coffee Chat bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="coffee", description="Open the Coffee Chat menu")
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
        
        # Create main menu view
        view = CoffeeChatMainView(
            request_callback=self.handle_request,
            view_requests_callback=self.handle_view_requests,
            stats_callback=self.handle_stats,
            leaderboard_callback=self.handle_leaderboard,
            cancel_callback=self.handle_cancel
        )
        
        # Send menu
        embed = discord.Embed(
            title="☕ Coffee Chat Menu",
            description="Welcome to Coffee Chat! Select an option below:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="What is Coffee Chat?",
            value="Coffee Chat allows you to connect with other users for one-on-one conversations about topics of interest.",
            inline=False
        )
        
        embed.add_field(
            name="How it works",
            value="1. Create a request with a topic\n2. Other users can accept your request\n3. Chat through DMs with the bot\n4. End the chat when you're done",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def handle_request(self, interaction: discord.Interaction):
        """Handle a user clicking the Request Coffee Chat button."""
        # Check if user already has a pending request
        existing_request = await get_user_request(interaction.user.id)
        if existing_request:
            await interaction.response.send_message(
                "You already have a pending coffee chat request. Please cancel it before creating a new one.",
                ephemeral=True
            )
            return
        
        # Check if user is in a guild
        if not interaction.guild:
            await interaction.response.send_message(
                "You must be in a server to create a coffee chat request.",
                ephemeral=True
            )
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
        
        # Send confirmation to user
        await interaction.response.send_message(
            "Your coffee chat request has been created!",
            embed=embed,
            ephemeral=True
        )
        
        # Send request to channel
        channel = interaction.channel
        
        # Create view with accept button
        class AcceptRequestView(discord.ui.View):
            def __init__(self, accept_callback):
                super().__init__(timeout=None)  # No timeout for request buttons
                self.accept_callback = accept_callback
            
            @discord.ui.button(label="Accept Request", style=discord.ButtonStyle.success, emoji="✅", custom_id=f"accept_request_{request['request_id']}")
            async def accept_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                await self.accept_callback(button_interaction, request['request_id'])
        
        view = AcceptRequestView(self.handle_accept_request)
        
        # Send request to channel
        await channel.send(
            f"**{interaction.user.display_name}** is looking for a coffee chat!",
            embed=embed,
            view=view
        )
    
    async def handle_view_requests(self, interaction: discord.Interaction):
        """Handle a user clicking the View Requests button."""
        # Get pending requests excluding the user's own
        requests = await get_pending_requests(exclude_user_id=interaction.user.id)
        
        if not requests:
            await interaction.response.send_message(
                "There are no pending coffee chat requests at the moment.",
                ephemeral=True
            )
            return
        
        # Create embed for requests
        embed = discord.Embed(
            title="☕ Pending Coffee Chat Requests",
            description=f"Found {len(requests)} pending requests. Select one to accept:",
            color=discord.Color.blue()
        )
        
        # Create view with request list
        view = RequestListView(requests, self.handle_accept_request)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def handle_accept_request(self, interaction: discord.Interaction, request_id):
        """Handle a user accepting a coffee chat request."""
        # Check if user is the requester
        requests = await get_pending_requests()
        request = next((r for r in requests if r['request_id'] == request_id), None)
        
        if not request:
            await interaction.response.send_message(
                "This request is no longer available.",
                ephemeral=True
            )
            return
        
        if request['user_id'] == interaction.user.id:
            await interaction.response.send_message(
                "You cannot accept your own request.",
                ephemeral=True
            )
            return
        
        # Check if user is already in a chat
        user_in_chat = await self.bot.message_handler.is_in_active_chat(interaction.user.id)
        if user_in_chat:
            await interaction.response.send_message(
                "You are already in an active coffee chat. Please end it before accepting a new one.",
                ephemeral=True
            )
            return
        
        # Check if requester is already in a chat
        requester_in_chat = await self.bot.message_handler.is_in_active_chat(request['user_id'])
        if requester_in_chat:
            await interaction.response.send_message(
                "The requester is already in an active coffee chat. Please try another request.",
                ephemeral=True
            )
            return
        
        # Create chat in database
        chat = await create_chat(
            request_id=request_id,
            user1_id=request['user_id'],
            user2_id=interaction.user.id
        )
        
        await interaction.response.send_message(
            "You've accepted the coffee chat request! Check your DMs to start chatting.",
            ephemeral=True
        )
        
        # Start chat in message handler
        success = await self.bot.message_handler.start_chat(chat)
        
        if not success:
            # If chat couldn't be started, notify the user
            await interaction.followup.send(
                "There was an error starting the chat. Please make sure you have DMs enabled.",
                ephemeral=True
            )
    
    async def handle_stats(self, interaction: discord.Interaction):
        """Handle a user clicking the My Stats button."""
        # Get user stats
        stats = await get_user_stats(interaction.user.id)
        
        if not stats:
            await interaction.response.send_message(
                "You haven't participated in any coffee chats yet.",
                ephemeral=True
            )
            return
        
        # Create stats embed
        embed = create_stats_embed(interaction.user, stats)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def handle_leaderboard(self, interaction: discord.Interaction):
        """Handle a user clicking the Leaderboard button."""
        # Get leaderboard
        leaderboard = await get_leaderboard(limit=10)
        
        # Create leaderboard embed
        embed = create_leaderboard_embed(leaderboard)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def handle_cancel(self, interaction: discord.Interaction):
        """Handle a user clicking the Cancel My Request button."""
        # Check if user has a pending request
        request = await get_user_request(interaction.user.id)
        
        if not request:
            await interaction.response.send_message(
                "You don't have any pending coffee chat requests.",
                ephemeral=True
            )
            return
        
        # Cancel request
        await cancel_request(request['request_id'])
        
        await interaction.response.send_message(
            "Your coffee chat request has been cancelled.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(CoffeeCommands(bot))
