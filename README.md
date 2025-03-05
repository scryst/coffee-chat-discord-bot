# ☕ Coffee Chat Discord Bot

A Discord bot that facilitates spontaneous coffee chats between server members, similar to Yggdrasil's telephone feature.

## Features

- 🔄 On-demand coffee chat requests at any time
- 👥 Simple accept/decline interface with interactive buttons
- 💬 Conversations take place through the bot's DMs
- 📊 Track coffee chat statistics and history
- 🔔 Direct message notifications for participants
- ⏱️ Duration tracking for coffee chats

## How It Works

1. A user requests a coffee chat using the `/coffee` command
2. The request appears in the channel with Accept/Decline buttons
3. When another user accepts, both users are connected through the bot's DMs
4. All messages sent to the bot are relayed to the other participant
5. Either user can end the chat when they're done with `/coffee_end`
6. Statistics are tracked for each user

## Commands

- `/coffee` - Request a coffee chat
- `/coffee_cancel` - Cancel your pending request
- `/coffee_end` - End your active coffee chat
- `/coffee_stats` - View your coffee chat statistics
- `/coffee_help` - Show help information

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```
4. Run the bot:
   ```
   python bot.py
   ```

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

## Requirements

- Python 3.8 or higher
- discord.py 2.0 or higher
- aiosqlite for database management
- python-dotenv for environment variables
- flask for Replit hosting
