import os
import discord
from discord import app_commands
from dotenv import load_dotenv
import logging
import asyncio
from database import Database
import io
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('coffee_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
REPLIT_SERVER = os.getenv('REPLIT_SERVER')

# Initialize database
db = Database()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot client
class CoffeeBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        # Initialize database
        await db.setup()
        logger.info("Database initialized")

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            # Sync commands with Discord
            await self.tree.sync()
            self.synced = True
            logger.info(f"Synced commands for {self.user}")
        
        logger.info(f"{self.user} is ready and online!")
        
        # Set the bot's presence with Discord link
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, 
                name="/coffee_help | discord.gg/KGE8BfruV4"
            )
        )
        
    async def on_guild_join(self, guild):
        """Register server and members when bot joins a new server"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Register the server
        await db.register_server(guild.id, guild.name)
        
        # Register all members
        for member in guild.members:
            if not member.bot:
                await db.register_user(member.id, str(member), member.avatar.url if member.avatar else None)
                await db.add_user_to_server(member.id, guild.id)
        
        logger.info(f"Registered {guild.name} and its members")
    
    async def on_member_join(self, member):
        """Register new members when they join a server"""
        if not member.bot:
            await db.register_user(member.id, str(member), member.avatar.url if member.avatar else None)
            await db.add_user_to_server(member.id, member.guild.id)
            logger.info(f"Registered new member: {member} in {member.guild.name}")
    
    async def on_interaction(self, interaction):
        """Handle button interactions"""
        if not interaction.type == discord.InteractionType.component:
            return
        
        # Let the Discord.py handle the interaction first
        if interaction.data.get('custom_id', '').startswith('accept_coffee:'):
            # Extract the request ID from the custom_id
            request_id = int(interaction.data['custom_id'].split(':')[1])
            
            # Check if user is the requester
            request_info = await db.get_user_coffee_request(interaction.user.id)
            if request_info and request_info['request_id'] == request_id:
                await interaction.response.send_message(
                    "You cannot accept your own coffee chat request!",
                    ephemeral=True
                )
                return
            
            # Check if user is already in a chat
            if await db.is_in_chat(interaction.user.id):
                await interaction.response.send_message(
                    "You are already in an active coffee chat. "
                    "Please finish your current chat before accepting a new one.",
                    ephemeral=True
                )
                return
            
            # Create the chat
            chat_info = await db.create_chat(request_id, interaction.user.id)
            
            if not chat_info:
                await interaction.response.send_message(
                    "Failed to create coffee chat. The request may no longer be available.",
                    ephemeral=True
                )
                return
            
            # Get the requester user
            requester = await client.fetch_user(chat_info['requester_id'])
            
            # Create DM channels
            requester_dm = await requester.create_dm()
            accepter_dm = await interaction.user.create_dm()
            
            # Notify both users
            embed = discord.Embed(
                title=f"☕ Coffee Chat Started: {chat_info['topic']}",
                description="You are now connected! Messages you send here will be relayed to the other person.",
                color=discord.Color.blue()
            )
            
            embed.set_footer(text="Join our community: discord.gg/KGE8BfruV4")
            
            # Add end chat button
            view = discord.ui.View(timeout=None)
            end_button = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="End Chat",
                custom_id=f"end_coffee:{chat_info['chat_id']}"
            )
            view.add_item(end_button)
            
            # Send to requester
            await requester_dm.send(
                f"**{interaction.user}** has accepted your coffee chat request!",
                embed=embed,
                view=view
            )
            
            # Send to accepter
            await accepter_dm.send(
                f"You have accepted **{requester}**'s coffee chat request!",
                embed=embed,
                view=view
            )
            
            # Update the original message
            try:
                await interaction.message.edit(
                    content=f"This coffee chat has been accepted by {interaction.user.mention}!",
                    embed=None,
                    view=None
                )
            except:
                pass
            
            await interaction.response.send_message(
                f"You have accepted the coffee chat! Check your DMs to start chatting with {requester.mention}.",
                ephemeral=True
            )
            
            logger.info(f"Created coffee chat between {requester} and {interaction.user}")
        
        elif interaction.data.get('custom_id', '').startswith('end_coffee:'):
            # Extract the chat ID from the custom_id
            chat_id = int(interaction.data['custom_id'].split(':')[1])
            
            # End the chat
            chat_info = await db.end_chat(interaction.user.id)
            
            if not chat_info:
                await interaction.response.send_message(
                    "You don't have an active coffee chat to end.",
                    ephemeral=True
                )
                return
            
            # Get the other user
            other_user_id = chat_info['requester_id'] if interaction.user.id == chat_info['accepter_id'] else chat_info['accepter_id']
            other_user = await client.fetch_user(other_user_id)
            
            # Format duration
            duration_minutes = chat_info['duration'] // 60
            duration_seconds = chat_info['duration'] % 60
            duration_str = f"{duration_minutes} minutes and {duration_seconds} seconds"
            
            # Create summary embed
            embed = discord.Embed(
                title="☕ Coffee Chat Ended",
                description=f"Your coffee chat about **{chat_info['topic']}** has ended.",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="Duration",
                value=duration_str,
                inline=True
            )
            
            embed.add_field(
                name="Chat Partner",
                value=str(other_user),
                inline=True
            )
            
            # Send to both users
            try:
                await interaction.channel.send(embed=embed)
            except:
                pass
            
            # Try to send to the other user's DM
            try:
                other_dm = await other_user.create_dm()
                await other_dm.send(
                    f"**{interaction.user}** has ended the coffee chat.",
                    embed=embed
                )
            except:
                pass
            
            await interaction.response.send_message(
                "You have ended the coffee chat. Thanks for participating!",
                ephemeral=True
            )
            
            logger.info(f"Ended coffee chat between {interaction.user.id} and {other_user_id}, duration: {duration_str}")

client = CoffeeBot()

# Helper function to register user and server during interactions
async def register_interaction_user(interaction):
    """Register user and server during command interactions"""
    user = interaction.user
    guild = interaction.guild
    
    # Register user
    await db.register_user(user.id, str(user), user.avatar.url if user.avatar else None)
    
    # Register server
    await db.register_server(guild.id, guild.name)
    
    # Add user to server
    await db.add_user_to_server(user.id, guild.id)

# Basic help command
@client.tree.command(name="coffee_help", description="Shows help information for Coffee Chat Bot")
async def coffee_help(interaction: discord.Interaction):
    await register_interaction_user(interaction)
    
    embed = discord.Embed(
        title="☕ Coffee Chat Bot Help",
        description="Connect with others through coffee chats!\nJoin our community: [discord.gg/KGE8BfruV4](https://discord.gg/KGE8BfruV4)",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Basic Commands",
        value=(
            "• `/coffee_help` - Shows this help message\n"
            "• `/coffee_request` - Create a new coffee chat request\n"
            "• `/coffee_cancel` - Cancel your pending coffee chat request\n"
            "• `/coffee_list` - List all pending coffee chat requests\n"
            "• `/coffee_stats` - View your coffee chat statistics\n"
            "• `/coffee_leaderboard` - View the coffee chat leaderboard\n"
        ),
        inline=False
    )
    
    embed.set_footer(text="Join our Discord community: discord.gg/KGE8BfruV4")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Create coffee request command
@client.tree.command(
    name="coffee_request", 
    description="Create a new coffee chat request"
)
@app_commands.describe(
    topic="The topic you want to discuss",
    description="A brief description of what you want to chat about",
    public="Make your request visible to users in other servers (default: True)"
)
async def coffee_request(
    interaction: discord.Interaction, 
    topic: str, 
    description: str, 
    public: bool = True
):
    await register_interaction_user(interaction)
    
    # Check if user already has an active request
    existing_request = await db.get_user_coffee_request(interaction.user.id)
    if existing_request:
        await interaction.response.send_message(
            "You already have an active coffee chat request. "
            "Please cancel it first with `/coffee_cancel` before creating a new one.",
            ephemeral=True
        )
        return
    
    # Check if user is in an active chat
    if await db.is_in_chat(interaction.user.id):
        await interaction.response.send_message(
            "You are currently in an active coffee chat. "
            "Please finish your current chat before creating a new request.",
            ephemeral=True
        )
        return
    
    # Create the request
    request_id = await db.create_coffee_request(
        interaction.user.id,
        interaction.guild.id,
        topic,
        description,
        public
    )
    
    if not request_id:
        await interaction.response.send_message(
            "Failed to create coffee chat request. Please try again later.",
            ephemeral=True
        )
        return
    
    # Create embed for the request
    embed = discord.Embed(
        title=f"☕ Coffee Chat: {topic}",
        description=description,
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="Requested by",
        value=interaction.user.mention,
        inline=True
    )
    
    embed.add_field(
        name="Visibility",
        value="Public (Cross-server)" if public else "Server Only",
        inline=True
    )
    
    embed.add_field(
        name="Community",
        value="[Join our Discord](https://discord.gg/KGE8BfruV4)",
        inline=True
    )
    
    embed.set_footer(text=f"Request ID: {request_id} • Use the buttons below to interact")
    
    # Create buttons for the request
    view = discord.ui.View(timeout=None)
    
    # Accept button
    accept_button = discord.ui.Button(
        style=discord.ButtonStyle.success,
        label="Accept Chat",
        custom_id=f"accept_coffee:{request_id}"
    )
    view.add_item(accept_button)
    
    # Send the message
    await interaction.response.send_message(
        "Your coffee chat request has been created!",
        ephemeral=True
    )
    
    # Send to channel
    await interaction.channel.send(embed=embed, view=view)
    logger.info(f"Created coffee request {request_id} for {interaction.user} in {interaction.guild.name}")

# Cancel coffee request command
@client.tree.command(
    name="coffee_cancel", 
    description="Cancel your pending coffee chat request"
)
async def coffee_cancel(interaction: discord.Interaction):
    await register_interaction_user(interaction)
    
    # Check if user has an active request
    request = await db.get_user_coffee_request(interaction.user.id)
    if not request:
        await interaction.response.send_message(
            "You don't have an active coffee chat request to cancel.",
            ephemeral=True
        )
        return
    
    # Cancel the request
    success = await db.cancel_coffee_request(request['request_id'], interaction.user.id)
    
    if not success:
        await interaction.response.send_message(
            "Failed to cancel your coffee chat request. Please try again later.",
            ephemeral=True
        )
        return
    
    await interaction.response.send_message(
        "Your coffee chat request has been cancelled.",
        ephemeral=True
    )
    
    logger.info(f"Cancelled coffee request {request['request_id']} for {interaction.user}")

# List coffee requests command
@client.tree.command(
    name="coffee_list", 
    description="List all open coffee chat requests"
)
@app_commands.describe(
    cross_server="Include requests from other servers (default: False)"
)
async def coffee_list(interaction: discord.Interaction, cross_server: bool = False):
    await register_interaction_user(interaction)
    
    # Get all open requests
    if cross_server:
        requests = await db.get_all_open_requests(exclude_user_id=interaction.user.id)
    else:
        requests = await db.get_all_open_requests(server_id=interaction.guild.id, exclude_user_id=interaction.user.id)
    
    if not requests:
        await interaction.response.send_message(
            f"No open coffee chat requests found{' across all servers' if cross_server else ' in this server'}.",
            ephemeral=True
        )
        return
    
    # Create embed for the requests
    embed = discord.Embed(
        title="☕ Open Coffee Chat Requests",
        description=f"Found {len(requests)} open requests{' across all servers' if cross_server else ' in this server'}.",
        color=discord.Color.blue()
    )
    
    # Add each request to the embed
    for i, request in enumerate(requests[:10]):  # Limit to 10 requests to avoid hitting embed limits
        embed.add_field(
            name=f"{i+1}. {request['topic']} (by {request['username']})",
            value=(
                f"**Description:** {request['description'][:100]}{'...' if len(request['description']) > 100 else ''}\n"
                f"**Server:** {request['server_name']}\n"
                f"**Created:** <t:{int(datetime.datetime.fromisoformat(str(request['created_at']).replace('Z', '+00:00')).timestamp())}:R>"
            ),
            inline=False
        )
    
    # Add note if there are more requests
    if len(requests) > 10:
        embed.set_footer(text=f"Showing 10 of {len(requests)} requests. Use the command again to see more.")
    
    # Create view with buttons for each request
    view = discord.ui.View(timeout=None)
    
    # Add buttons for each request (up to 5 due to Discord UI limitations)
    for i, request in enumerate(requests[:5]):
        button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label=f"Accept #{i+1}",
            custom_id=f"accept_coffee:{request['request_id']}"
        )
        view.add_item(button)
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    logger.info(f"Listed {len(requests)} coffee requests for {interaction.user}")

# Message relay event
@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return
    
    # Only process DM messages
    if not isinstance(message.channel, discord.DMChannel):
        return
    
    # Check if user is in an active chat
    chat_info = await db.get_active_chat(message.author.id)
    if not chat_info:
        return
    
    # Get the other user
    other_user = await client.fetch_user(chat_info['other_user_id'])
    
    # Create DM channel with the other user
    other_dm = await other_user.create_dm()
    
    # Format the message
    content = f"**{message.author}:** {message.content}"
    
    # Handle attachments
    files = []
    for attachment in message.attachments:
        try:
            file_bytes = await attachment.read()
            discord_file = discord.File(
                fp=io.BytesIO(file_bytes),
                filename=attachment.filename
            )
            files.append(discord_file)
        except Exception as e:
            logger.error(f"Failed to relay attachment: {e}")
    
    # Store the message in the database
    has_attachment = len(files) > 0
    await db.store_message(
        chat_info['chat_id'],
        message.author.id,
        message.content,
        has_attachment
    )
    
    # Relay the message
    try:
        await other_dm.send(content=content, files=files)
        logger.info(f"Relayed message from {message.author.id} to {other_user.id}")
    except Exception as e:
        logger.error(f"Failed to relay message: {e}")
        await message.channel.send("Failed to send your message to the other user. They may have blocked the bot.")

# User stats command
@client.tree.command(
    name="coffee_stats", 
    description="View your coffee chat statistics"
)
async def coffee_stats(interaction: discord.Interaction):
    await register_interaction_user(interaction)
    
    # Get user stats
    stats = await db.get_user_stats(interaction.user.id)
    
    # Create embed for the stats
    embed = discord.Embed(
        title=f"☕ Coffee Chat Stats for {interaction.user}",
        color=discord.Color.blue()
    )
    
    # Format times
    total_hours = stats['total_duration'] // 3600
    total_minutes = (stats['total_duration'] % 3600) // 60
    
    avg_minutes = stats['avg_duration'] // 60
    avg_seconds = stats['avg_duration'] % 60
    
    max_minutes = stats['max_duration'] // 60
    max_seconds = stats['max_duration'] % 60
    
    # Add stats to the embed
    embed.add_field(
        name="Total Chats",
        value=str(stats['total_chats']),
        inline=True
    )
    
    embed.add_field(
        name="Total Time",
        value=f"{total_hours}h {total_minutes}m" if stats['total_duration'] > 0 else "0m",
        inline=True
    )
    
    embed.add_field(
        name="Unique Partners",
        value=str(stats['unique_partners']),
        inline=True
    )
    
    embed.add_field(
        name="Chats Initiated",
        value=str(stats['chats_initiated']),
        inline=True
    )
    
    embed.add_field(
        name="Chats Accepted",
        value=str(stats['chats_accepted']),
        inline=True
    )
    
    embed.add_field(
        name="Average Duration",
        value=f"{avg_minutes}m {avg_seconds}s" if stats['avg_duration'] > 0 else "0m",
        inline=True
    )
    
    embed.add_field(
        name="Longest Chat",
        value=f"{max_minutes}m {max_seconds}s" if stats['max_duration'] > 0 else "0m",
        inline=True
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"Displayed stats for {interaction.user}")

# Leaderboard command
@client.tree.command(
    name="coffee_leaderboard", 
    description="View the coffee chat leaderboard"
)
@app_commands.describe(
    server_only="Show only users from this server (default: True)"
)
async def coffee_leaderboard(interaction: discord.Interaction, server_only: bool = True):
    await register_interaction_user(interaction)
    
    # Get leaderboard
    if server_only:
        leaderboard = await db.get_leaderboard(server_id=interaction.guild.id)
    else:
        leaderboard = await db.get_leaderboard()
    
    if not leaderboard:
        await interaction.response.send_message(
            "No coffee chat data found for the leaderboard.",
            ephemeral=True
        )
        return
    
    # Create embed for the leaderboard
    embed = discord.Embed(
        title="☕ Coffee Chat Leaderboard",
        description=f"Top chatters{' in this server' if server_only else ''}",
        color=discord.Color.gold()
    )
    
    # Add leaderboard entries
    for i, entry in enumerate(leaderboard):
        # Format time
        hours = entry['total_duration'] // 3600
        minutes = (entry['total_duration'] % 3600) // 60
        time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Add medal emoji for top 3
        medal = ""
        if i == 0:
            medal = "🥇 "
        elif i == 1:
            medal = "🥈 "
        elif i == 2:
            medal = "🥉 "
        
        embed.add_field(
            name=f"{medal}#{i+1}: {entry['username']}",
            value=f"**Chats:** {entry['chat_count']} | **Time:** {time_str}",
            inline=False
        )
    
    embed.set_footer(text="Join our community: discord.gg/KGE8BfruV4")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)
    logger.info(f"Displayed leaderboard for {interaction.user}")

# Run the bot
if __name__ == "__main__":
    if TOKEN:
        # Start keep-alive server if running on Replit
        if REPLIT_SERVER:
            try:
                from keep_alive import keep_alive
                keep_alive()
                logger.info("Started keep-alive server for Replit")
            except Exception as e:
                logger.error(f"Failed to start keep-alive server: {e}")
        
        # Run the bot
        client.run(TOKEN)
    else:
        logger.error("No Discord token found. Please set the DISCORD_TOKEN environment variable.")
