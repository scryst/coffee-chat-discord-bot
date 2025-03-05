# ☕ Coffee Chat Discord Bot

A Discord bot that facilitates coffee chats between users across servers, allowing for networking and knowledge sharing.

## Join Our Community

Join our Discord community to get help, share feedback, and connect with other users:
[Join the Discord server](https://discord.gg/KGE8BfruV4)

## Features

- 🔄 Create coffee chat requests with topics and descriptions
- 🌐 Cross-server functionality to connect with users from different servers
- 👥 Simple menu-based UI with interactive buttons
- 💬 Private conversations through the bot's DMs
- 📊 Comprehensive statistics and leaderboards
- 🔔 Direct message notifications for participants
- ⏱️ Duration tracking for coffee chats
- 📁 Support for file and image sharing during chats

## Commands

The bot uses a single command with a menu-based UI:

- `/coffee` - Opens the main menu with buttons for all functionality

## Menu Options

From the main menu, users can:
- **Request Coffee Chat** - Create a new coffee chat request
- **View Requests** - Browse and accept pending coffee chat requests
- **My Stats** - View personal coffee chat statistics
- **Leaderboard** - View the coffee chat leaderboard
- **Cancel My Request** - Cancel your pending coffee chat request

## How It Works

1. A user opens the menu with `/coffee` and selects "Request Coffee Chat"
2. They fill out a modal with topic and description
3. The request appears in the channel with an Accept button
4. Other users can view and accept requests through the menu
5. When another user accepts, both users are connected through the bot's DMs
6. All messages sent to the bot are relayed to the other participant
7. Either user can end the chat by clicking the "End Chat" button
8. Statistics are tracked for each user and displayed on leaderboards

## Setup

1. Clone this repository
2. Install dependencies with `pip install -r requirements.txt`
3. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```
4. Run the bot with `python bot.py`

## Database

The bot uses SQLite to store:
- User information
- Server information
- Coffee chat requests
- Active chats
- Chat history
- Message history
- Statistics for leaderboards

## Hosting on Replit

1. Create a new Replit project
2. Upload all files from this repository
3. Add your Discord bot token as a secret named `DISCORD_TOKEN`
4. Click Run to start the bot
5. Set up UptimeRobot to ping the Replit URL to keep it running

## Setup Your Own Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and add a bot
3. Enable the necessary intents (Members and Message Content)
4. Generate an invite link with the `bot` and `applications.commands` scopes
5. Invite the bot to your server
6. Run the bot using your token

## Required Permissions

The bot requires the following permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Use Slash Commands
- Read Message History

## Privacy Considerations

- All messages sent during coffee chats are relayed through the bot
- Message content is stored in the database for record-keeping
- Users can end chats at any time
- The bot only processes messages in DMs during active coffee chats

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Requirements

- Python 3.8 or higher
- discord.py 2.0 or higher
- aiosqlite for database management
- python-dotenv for environment variables
- flask for Replit hosting
