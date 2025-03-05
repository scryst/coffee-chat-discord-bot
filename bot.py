import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import datetime
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)
db = Database()

# Message cache for DM conversations
message_cache = {}

# Define view for coffee chat request buttons
class CoffeeChatRequestView(discord.ui.View):
    def __init__(self, requester_id, timeout=180):
        super().__init__(timeout=timeout)
        self.requester_id = requester_id
        self.value = None
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="☕")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only allow users other than the requester to accept
        if interaction.user.id == self.requester_id:
            await interaction.response.send_message("You can't accept your own coffee chat request!", ephemeral=True)
            return
        
        # Check if the accepting user is already in a call
        if await db.is_in_call(interaction.user.id):
            await interaction.response.send_message("You're already in an active coffee chat!", ephemeral=True)
            return
        
        # Check if the requester is still available
        if not await db.has_pending_request(self.requester_id, interaction.guild.id):
            await interaction.response.send_message("This coffee chat request is no longer available.", ephemeral=True)
            self.stop()
            return
        
        # Get user objects
        requester = interaction.guild.get_member(self.requester_id)
        accepter = interaction.user
        
        if not requester:
            await interaction.response.send_message("The requester seems to have left the server.", ephemeral=True)
            self.stop()
            return
        
        # Create the call in the database
        await db.create_call(self.requester_id, interaction.user.id, interaction.guild.id)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(content=f"☕ {accepter.mention} has accepted {requester.mention}'s coffee chat request! Enjoy your conversation!", view=self)
        
        # Create a DM channel for both users through the bot
        try:
            # Initialize message cache for this conversation
            chat_id = f"{min(requester.id, accepter.id)}_{max(requester.id, accepter.id)}"
            message_cache[chat_id] = []
            
            # Send initial messages to both users
            requester_dm = await requester.create_dm()
            accepter_dm = await accepter.create_dm()
            
            # Create message relay view
            requester_view = MessageRelayView(requester.id, accepter.id, chat_id)
            accepter_view = MessageRelayView(accepter.id, requester.id, chat_id)
            
            # Send welcome messages with the chat controls
            await requester_dm.send(
                f"☕ **Coffee Chat Started!**\n\nYou're now chatting with {accepter.mention}. Type your messages here and they'll be relayed to them.\n"
                f"Use `/coffee_end` in the server to end this chat when you're done.",
                view=requester_view
            )
            
            await accepter_dm.send(
                f"☕ **Coffee Chat Started!**\n\nYou're now chatting with {requester.mention}. Type your messages here and they'll be relayed to them.\n"
                f"Use `/coffee_end` in the server to end this chat when you're done.",
                view=accepter_view
            )
        except Exception as e:
            print(f"Error setting up DM channels: {e}")
        
        self.value = True
        self.stop()
    
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only allow users other than the requester to decline
        if interaction.user.id == self.requester_id:
            await interaction.response.send_message("You can't decline your own coffee chat request!", ephemeral=True)
            return
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(content="This coffee chat request has been declined.", view=self)
        self.value = False
        self.stop()

# Define view for message relay in DMs
class MessageRelayView(discord.ui.View):
    def __init__(self, user_id, target_id, chat_id):
        super().__init__(timeout=None)  # No timeout for these controls
        self.user_id = user_id
        self.target_id = target_id
        self.chat_id = chat_id
    
    @discord.ui.button(label="End Chat", style=discord.ButtonStyle.danger, emoji="🔚", custom_id="end_coffee_chat_dm")
    async def end_call(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user is part of this call
        call = await db.get_active_call(interaction.user.id)
        if not call:
            await interaction.response.send_message("You don't have an active coffee chat to end.")
            return
        
        # End the call
        result = await db.end_call(interaction.user.id)
        if not result:
            await interaction.response.send_message("Failed to end the coffee chat. Please try again.")
            return
        
        # Get the other user
        other_user = await bot.fetch_user(call["other_user_id"])
        other_user_mention = other_user.mention if other_user else "the other participant"
        
        # Calculate duration
        started_at = datetime.datetime.fromisoformat(str(call["started_at"]).replace('Z', '+00:00'))
        duration = datetime.datetime.now(datetime.timezone.utc) - started_at.replace(tzinfo=datetime.timezone.utc)
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        
        # Disable the button
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"☕ Coffee chat ended! Duration: {minutes}m {seconds}s")
        
        # Try to DM the other user
        if other_user:
            try:
                other_dm = await other_user.create_dm()
                await other_dm.send(f"☕ Your coffee chat with {interaction.user.mention} has been ended. It lasted {minutes}m {seconds}s.")
            except:
                pass
        
        # Clear the message cache for this chat
        if self.chat_id in message_cache:
            del message_cache[self.chat_id]

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await db.setup()
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if this is a DM
    if isinstance(message.channel, discord.DMChannel):
        # Check if the user is in an active call
        if await db.is_in_call(message.author.id):
            # Get call info
            call_info = await db.get_active_call(message.author.id)
            other_user_id = call_info["other_user_id"]
            
            # Create a chat ID (consistent regardless of who messages first)
            chat_id = f"{min(message.author.id, other_user_id)}_{max(message.author.id, other_user_id)}"
            
            # Store message in cache
            if chat_id not in message_cache:
                message_cache[chat_id] = []
            message_cache[chat_id].append({
                "author_id": message.author.id,
                "content": message.content,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Relay the message to the other user
            try:
                other_user = await bot.fetch_user(other_user_id)
                other_dm = await other_user.create_dm()
                
                # Handle attachments if any
                files = []
                for attachment in message.attachments:
                    files.append(await attachment.to_file())
                
                # Send the message
                await other_dm.send(f"**{message.author.display_name}**: {message.content}", files=files if files else None)
            except Exception as e:
                print(f"Error relaying message: {e}")
                await message.channel.send("Failed to relay your message. The other user may have blocked the bot or left the server.")
    
    # Process commands
    await bot.process_commands(message)

@bot.tree.command(name="coffee", description="Request a random coffee chat with someone")
async def coffee_request(interaction: discord.Interaction):
    # Register the user if they're not already in the database
    await db.register_user(interaction.user.id, str(interaction.user), interaction.guild.id)
    
    # Check if user is already in a call
    if await db.is_in_call(interaction.user.id):
        call_info = await db.get_active_call(interaction.user.id)
        other_user = interaction.guild.get_member(call_info["other_user_id"])
        other_user_mention = other_user.mention if other_user else "another user"
        
        await interaction.response.send_message(
            f"☕ You're already in an active coffee chat with {other_user_mention}!",
            ephemeral=True
        )
        return
    
    # Check if user already has a pending request
    if await db.has_pending_request(interaction.user.id, interaction.guild.id):
        await interaction.response.send_message(
            "☕ You already have a pending coffee chat request. Use `/coffee_cancel` to cancel it.",
            ephemeral=True
        )
        return
    
    # Create a new request
    success = await db.create_request(interaction.user.id, interaction.guild.id)
    if not success:
        await interaction.response.send_message(
            "Failed to create coffee chat request. Please try again later.",
            ephemeral=True
        )
        return
    
    # Create the request view
    view = CoffeeChatRequestView(interaction.user.id)
    
    # Send the request to the channel
    await interaction.response.send_message(
        f"☕ {interaction.user.mention} is looking for a coffee chat partner! Click Accept to join them for a conversation.",
        view=view
    )
    
    # Wait for someone to accept or for the view to time out
    timeout = await view.wait()
    
    if timeout or view.value is None:
        # If timed out or no response, cancel the request
        await db.cancel_request(interaction.user.id, interaction.guild.id)
        try:
            await interaction.edit_original_response(
                content=f"☕ {interaction.user.mention}'s coffee chat request has expired.",
                view=None
            )
        except:
            pass

@bot.tree.command(name="coffee_cancel", description="Cancel your pending coffee chat request")
async def coffee_cancel(interaction: discord.Interaction):
    # Check if user has a pending request
    if not await db.has_pending_request(interaction.user.id, interaction.guild.id):
        await interaction.response.send_message(
            "You don't have a pending coffee chat request to cancel.",
            ephemeral=True
        )
        return
    
    # Cancel the request
    await db.cancel_request(interaction.user.id, interaction.guild.id)
    
    await interaction.response.send_message(
        "☕ Your coffee chat request has been cancelled.",
        ephemeral=True
    )
    
    # Try to edit the original request message if possible
    try:
        # This is a bit tricky since we don't store the message ID
        # In a full implementation, you might want to store this
        channel = interaction.channel
        async for message in channel.history(limit=50):
            if message.author == bot.user and f"{interaction.user.mention} is looking for a coffee chat partner" in message.content:
                await message.edit(content=f"☕ {interaction.user.mention}'s coffee chat request has been cancelled.", view=None)
                break
    except:
        pass

@bot.tree.command(name="coffee_end", description="End your active coffee chat")
async def coffee_end(interaction: discord.Interaction):
    # Check if user is in a call
    if not await db.is_in_call(interaction.user.id):
        await interaction.response.send_message(
            "You don't have an active coffee chat to end.",
            ephemeral=True
        )
        return
    
    # Get call info
    call_info = await db.get_active_call(interaction.user.id)
    other_user = interaction.guild.get_member(call_info["other_user_id"])
    other_user_mention = other_user.mention if other_user else "the other participant"
    
    # End the call
    result = await db.end_call(interaction.user.id)
    if not result:
        await interaction.response.send_message(
            "Failed to end the coffee chat. Please try again.",
            ephemeral=True
        )
        return
    
    # Calculate duration
    started_at = datetime.datetime.fromisoformat(str(call_info["started_at"]).replace('Z', '+00:00'))
    duration = datetime.datetime.now(datetime.timezone.utc) - started_at.replace(tzinfo=datetime.timezone.utc)
    minutes = int(duration.total_seconds() // 60)
    seconds = int(duration.total_seconds() % 60)
    
    await interaction.response.send_message(
        f"☕ Coffee chat with {other_user_mention} has ended! It lasted {minutes}m {seconds}s."
    )
    
    # Try to DM the other user
    if other_user:
        try:
            await other_user.send(f"☕ Your coffee chat with {interaction.user.mention} has been ended. It lasted {minutes}m {seconds}s.")
        except:
            pass
    
    # Clear the message cache for this chat
    chat_id = f"{min(interaction.user.id, call_info['other_user_id'])}_{max(interaction.user.id, call_info['other_user_id'])}"
    if chat_id in message_cache:
        del message_cache[chat_id]

@bot.tree.command(name="coffee_stats", description="View your coffee chat statistics")
async def coffee_stats(interaction: discord.Interaction):
    # Get user stats
    stats = await db.get_call_stats(interaction.user.id, interaction.guild.id)
    
    # Create embed
    embed = discord.Embed(
        title="☕ Coffee Chat Statistics",
        description=f"Stats for {interaction.user.mention}",
        color=discord.Color.orange()
    )
    
    embed.add_field(
        name="Total Coffee Chats",
        value=str(stats["total_calls"]),
        inline=True
    )
    
    # Format total duration
    total_minutes = stats["total_duration"] // 60
    total_hours = total_minutes // 60
    remaining_minutes = total_minutes % 60
    
    duration_str = f"{total_hours}h {remaining_minutes}m" if total_hours > 0 else f"{total_minutes}m"
    
    embed.add_field(
        name="Total Time Spent",
        value=duration_str,
        inline=True
    )
    
    # Add average duration if there were any calls
    if stats["total_calls"] > 0:
        avg_duration = stats["total_duration"] / stats["total_calls"]
        avg_minutes = int(avg_duration // 60)
        avg_seconds = int(avg_duration % 60)
        
        embed.add_field(
            name="Average Duration",
            value=f"{avg_minutes}m {avg_seconds}s",
            inline=True
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="coffee_help", description="Learn how to use the Coffee Chat bot")
async def coffee_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="☕ Coffee Chat Bot Help",
        description="Connect with your community through spontaneous coffee chats!",
        color=discord.Color.orange()
    )
    
    embed.add_field(
        name="/coffee",
        value="Request a coffee chat. This sends a message to the channel that others can accept.",
        inline=False
    )
    
    embed.add_field(
        name="/coffee_cancel",
        value="Cancel your pending coffee chat request.",
        inline=False
    )
    
    embed.add_field(
        name="/coffee_end",
        value="End your active coffee chat.",
        inline=False
    )
    
    embed.add_field(
        name="/coffee_stats",
        value="View your coffee chat statistics.",
        inline=False
    )
    
    embed.add_field(
        name="How it works",
        value="When you request a coffee chat, others can accept your invitation. "
              "Once accepted, you'll both be connected through the bot's DMs. "
              "All messages you send to the bot will be relayed to your chat partner. "
              "When you're done, use `/coffee_end` to end the chat.",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    # For Replit hosting
    keep_alive_server = os.getenv('REPLIT_SERVER')
    if keep_alive_server:
        from keep_alive import keep_alive
        keep_alive()
    
    bot.run(TOKEN)
