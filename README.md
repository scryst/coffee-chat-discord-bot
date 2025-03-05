# ☕ Coffee Chat Discord Bot

A Discord bot that facilitates coffee chats between users across servers, allowing for networking and knowledge sharing.

## Features

- 🔄 Create coffee chat requests with topics and descriptions
- 🌐 Cross-server functionality to connect with users from different servers
- 👥 Simple accept interface with interactive buttons
- 💬 Private conversations through the bot's DMs
- 📊 Comprehensive statistics and leaderboards
- 🔔 Direct message notifications for participants
- ⏱️ Duration tracking for coffee chats
- 📁 Support for file and image sharing during chats

## Commands

- `/coffee_help` - Shows help information for the bot
- `/coffee_request` - Create a new coffee chat request with a topic and description
- `/coffee_cancel` - Cancel your pending coffee chat request
- `/coffee_list` - List all pending coffee chat requests (with option to view cross-server)
- `/coffee_stats` - View your personal coffee chat statistics
- `/coffee_leaderboard` - View the coffee chat leaderboard (server or global)

## How It Works

1. A user creates a coffee chat request using `/coffee_request` with a topic and description
2. The request appears in the channel with an Accept button
3. Other users can view available requests with `/coffee_list` (including cross-server requests)
4. When another user accepts, both users are connected through the bot's DMs
5. All messages sent to the bot are relayed to the other participant
6. Either user can end the chat by clicking the "End Chat" button
7. Statistics are tracked for each user and displayed on leaderboards

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

## Community

Join our Discord community: [https://discord.gg/KGE8BfruV4](https://discord.gg/KGE8BfruV4)

## Requirements

- Python 3.8 or higher
- discord.py 2.0 or higher
- aiosqlite for database management
- python-dotenv for environment variables
- flask for Replit hosting
