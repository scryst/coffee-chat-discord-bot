import discord
from discord import ui
import logging
from datetime import datetime

logger = logging.getLogger('coffee_bot.ui')

class CoffeeChatRequestModal(ui.Modal, title="Coffee Chat Request"):
    """Modal for creating a coffee chat request."""
    
    topic = ui.TextInput(
        label="Topic",
        placeholder="What would you like to discuss?",
        min_length=3,
        max_length=100,
        required=True
    )
    
    description = ui.TextInput(
        label="Description",
        placeholder="Provide more details about your topic...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )
    
    def __init__(self, callback):
        super().__init__()
        self.callback_func = callback
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.topic.value, self.description.value)

class CoffeeChatView(ui.View):
    """Main menu view for the coffee chat bot."""
    
    def __init__(self, request_callback, view_requests_callback, stats_callback, 
                 leaderboard_callback, cancel_callback):
        super().__init__(timeout=300)  # 5 minute timeout
        self.request_callback = request_callback
        self.view_requests_callback = view_requests_callback
        self.stats_callback = stats_callback
        self.leaderboard_callback = leaderboard_callback
        self.cancel_callback = cancel_callback
        
        # Add community button
        self.add_item(discord.ui.Button(
            label="Join our community",
            url="https://discord.gg/KGE8BfruV4",
            style=discord.ButtonStyle.link,
            emoji="🌐"
        ))
    
    @ui.button(label="Request Coffee Chat", style=discord.ButtonStyle.primary, emoji="☕")
    async def request_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.request_callback(interaction)
    
    @ui.button(label="Cross-Server Requests", style=discord.ButtonStyle.secondary, emoji="🔍")
    async def view_requests_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.view_requests_callback(interaction)
    
    @ui.button(label="My Stats", style=discord.ButtonStyle.secondary, emoji="📊")
    async def stats_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.stats_callback(interaction)
    
    @ui.button(label="Leaderboard", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def leaderboard_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.leaderboard_callback(interaction)
    
    @ui.button(label="Cancel My Request", style=discord.ButtonStyle.danger, emoji="⚫")
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.cancel_callback(interaction)

class RequestListView(ui.View):
    """View for displaying a list of chat requests."""
    
    def __init__(self, requests, accept_callback):
        super().__init__(timeout=300)  # 5 minute timeout
        self.requests = requests
        self.accept_callback = accept_callback
        
        # Add a select menu if there are requests
        if requests:
            self.add_request_select()
    
    def add_request_select(self):
        select = RequestSelect(self.requests, self.accept_callback)
        self.add_item(select)

class RequestSelect(ui.Select):
    """Select menu for chat requests."""
    
    def __init__(self, requests, accept_callback):
        self.requests = requests
        self.accept_callback = accept_callback
        
        # Create options from requests
        options = []
        for req in requests[:25]:  # Discord limits to 25 options
            topic = req['topic']
            if len(topic) > 50:
                topic = topic[:47] + "..."
            
            # Create description that includes the request description if available
            user_info = f"From {req['requester_name']} in {req['server_name']}"
            description = req.get('description', '')
            
            # Truncate description if needed
            if description and len(description) > 50:
                description = description[:47] + "..."
                
            # Combine user info and description if description exists
            display_description = f"{user_info} - {description}" if description else user_info
            
            # Ensure the description isn't too long for Discord's limits
            if len(display_description) > 100:
                display_description = display_description[:97] + "..."
            
            options.append(
                discord.SelectOption(
                    label=f"{topic}",
                    description=display_description,
                    value=str(req['request_id'])
                )
            )
        
        super().__init__(
            placeholder="Select a request to accept...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        request_id = int(self.values[0])
        
        # Find the selected request
        selected_request = next((r for r in self.requests if r['request_id'] == request_id), None)
        
        # Check if user is trying to accept their own request
        if selected_request and selected_request['user_id'] == interaction.user.id:
            await interaction.response.send_message(
                "You cannot accept your own coffee chat request.",
                ephemeral=True
            )
            return
            
        await self.accept_callback(interaction, request_id)

class ChatView(ui.View):
    """View for an active chat."""
    
    def __init__(self, end_callback):
        super().__init__(timeout=None)  # No timeout for active chats
        self.end_callback = end_callback
    
    @ui.button(label="End Chat", style=discord.ButtonStyle.danger, emoji="🛑")
    async def end_chat_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.end_callback(interaction)

def create_request_embed(request, user):
    """Create an embed for a chat request."""
    embed = discord.Embed(
        title=f"Coffee Chat Request: {request['topic']}",
        description=request['description'] if request['description'] else "No additional details provided.",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Requested by", value=f"{user.display_name} ({user.name})", inline=True)
    embed.add_field(name="Status", value="Pending", inline=True)
    embed.set_footer(text=f"Request ID: {request['request_id']}")
    embed.timestamp = discord.utils.utcnow()
    
    return embed

def create_completed_request_embed(request_id, chat_data, responder_name):
    """Create an embed for a completed chat request."""
    embed = discord.Embed(
        title=f"Completed Coffee Chat: {chat_data['topic']}",
        description=chat_data['description'] if chat_data.get('description') else "No additional details provided.",
        color=discord.Color.green()
    )
    
    # Calculate duration in minutes
    try:
        # Handle string ISO format or datetime objects
        if isinstance(chat_data['started_at'], str):
            start_time = datetime.fromisoformat(chat_data['started_at'])
        else:
            start_time = chat_data['started_at']
            
        if isinstance(chat_data['ended_at'], str):
            end_time = datetime.fromisoformat(chat_data['ended_at'])
        else:
            end_time = chat_data['ended_at']
            
        duration = max(1, int((end_time - start_time).total_seconds() / 60))
    except (ValueError, TypeError, KeyError) as e:
        # Fallback to a default duration if there's an error
        duration = chat_data.get('duration', 1)
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
    
    # We're now passing in the full formatted name from message_handler.py
    embed.add_field(name="Requested by", value=chat_data['user1_name'], inline=True)
    embed.add_field(name="Accepted by", value=responder_name, inline=True)
    embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
    embed.add_field(name="Status", value="Completed ✅", inline=True)
    embed.add_field(name="Ended", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
    
    # Only include the chat_id in the footer since request_id is redundant
    embed.set_footer(text=f"Chat ID: {chat_data['chat_id']}")
    embed.timestamp = discord.utils.utcnow()
    
    return embed

def create_stats_embed(user, stats):
    """Create an embed for user stats."""
    embed = discord.Embed(
        title=f"Coffee Chat Stats for {user.display_name}",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Total Chats", value=stats['total_chats'], inline=True)
    embed.add_field(name="Total Chat Time", value=f"{stats['total_time']} minutes", inline=True)
    
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"User ID: {user.id}")
    embed.timestamp = discord.utils.utcnow()
    
    return embed

def create_leaderboard_embed(leaderboard):
    """Create an embed for the leaderboard."""
    embed = discord.Embed(
        title="☕ Coffee Chat Leaderboard ☕",
        description="Top users by number of completed coffee chats",
        color=discord.Color.gold()
    )
    
    if not leaderboard:
        embed.add_field(name="No data yet", value="Be the first to complete a coffee chat!")
        return embed
    
    # Format leaderboard entries
    for i, entry in enumerate(leaderboard, 1):
        name = f"{i}. {entry['username']}"
        value = f"Chats: {entry['total_chats']} | Time: {entry['total_time']} min"
        embed.add_field(name=name, value=value, inline=False)
    
    embed.set_footer(text="Start a coffee chat to join the leaderboard!")
    embed.timestamp = discord.utils.utcnow()
    
    return embed
