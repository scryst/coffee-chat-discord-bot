# ☕ Coffee Chat Discord Bot

A Discord bot that facilitates professional networking through structured, bot-mediated coffee chat interactions across servers, allowing for networking and knowledge sharing.

## Join Our Community

Join our Discord community to get help, share feedback, and connect with other users:
[Join the Discord server](https://discord.gg/KGE8BfruV4)

## Features

- 🔄 Create coffee chat requests with topics and descriptions
- 🌐 Cross-server functionality to connect with users from different servers
- 👥 Simple menu-based UI with interactive buttons that adapt to user's current state
- 💬 Private conversations through the bot's DMs
- 📊 Comprehensive statistics tracking for users
- 🔔 Direct message notifications for participants
- ⏱️ Duration tracking for coffee chats
- 📁 Support for file and image sharing during chats
- 👤 Display of both username and display name for better identification
- 🎨 Stylized messages and embeds with consistent color schemes for different chat states
- 🔄 Dynamic UI updates with in-place message editing
- 🔒 Robust state management to prevent conflicting actions
- 🕒 Consistent timestamp formatting across all chat stages
- 🚫 Automatic cancellation of pending requests when accepting another request
- 🔄 Smart button visibility based on user's current state

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
- **End Current Chat** - End your active coffee chat (only shown when in an active chat)

## How It Works

1. A user opens the menu with `/coffee` and selects "Request Coffee Chat"
2. They fill out a modal with topic and description
3. The request appears in the channel with an Accept button
4. Other users can view and accept requests through the menu
5. When another user accepts, both users are connected through the bot's DMs
6. All messages sent to the bot are relayed to the other participant with display name and username
7. Either user can end the chat by clicking the "End Chat" button
8. After ending a chat, users receive a stylized summary with chat duration
9. Statistics are tracked for each user and displayed on leaderboards
10. "Coffee Chat In Progress" messages automatically update to "Coffee Chat Completed" after the chat ends
11. Chat status updates appear in both the server where the request was made and the server/DM where it was accepted
12. Accepting a cross-server request automatically cancels your current request if you have one
13. Users cannot create multiple requests or join chats while in an active chat
14. The UI dynamically adapts to show only relevant options based on the user's current state

## User State Management

The bot implements sophisticated state management to track:
- If a user is in an active chat
- If a user has a pending request
- If a user has no active interactions

This state management ensures users can only perform actions that make sense for their current state:
- Users in active chats see "End Current Chat" instead of "Request Coffee Chat"
- Users cannot create multiple requests
- Users cannot accept requests while in an active chat
- Users cannot cancel requests while in an active chat

## Setup

1. Clone this repository
2. Install dependencies with `pip install -r requirements.txt`
3. Create a `.env` file with your Discord bot token and other credentials:
   ```
   # Required
   DISCORD_TOKEN=your_discord_bot_token_here
   
   # Optional but recommended
   DISCORD_CLIENT_ID=your_client_id_here
   DISCORD_PUBLIC_KEY=your_public_key_here
   DISCORD_CLIENT_SECRET=your_client_secret_here
   
   # OAuth URL (generated with generate_oauth_url.py)
   DISCORD_OAUTH_URL=your_oauth_url_here
   ```

### Running on Windows

For Windows users, a PowerShell script is included to make starting the bot easier:
1. Run `create_shortcut.ps1` to create a desktop shortcut (one-time setup)
2. Use the created shortcut "Start Coffee Chat Bot" or run `start_coffee_bot.ps1` directly

### Environment Variables

The bot uses the following environment variables:
- `DISCORD_TOKEN` (required): Your Discord bot token
- `DISCORD_CLIENT_ID`: Your Discord application client ID
- `DISCORD_PUBLIC_KEY`: Your Discord application public key
- `DISCORD_CLIENT_SECRET`: Your Discord application client secret
- `DISCORD_OAUTH_URL`: The OAuth URL for inviting the bot (can be generated with `generate_oauth_url.py`)

A sample `.env.sample` file is provided as a template. Copy this to `.env` and fill in your values.

## Database Schema

The bot uses SQLite with the following tables:

### users
- `user_id` (PRIMARY KEY): Discord user ID
- `username`: Discord username
- `display_name`: Discord display name
- `created_at`: When the user was first added to the database

### servers
- `server_id` (PRIMARY KEY): Discord server ID
- `server_name`: Discord server name
- `created_at`: When the server was first added to the database

### coffee_requests
- `request_id` (PRIMARY KEY): Unique identifier for the request
- `user_id`: User who created the request
- `server_id`: Server where the request was created
- `channel_id`: Channel where the request was created
- `message_id`: Message ID of the request
- `topic`: Topic of the coffee chat
- `description`: Description of the coffee chat
- `created_at`: When the request was created
- `status`: Status of the request (pending, accepted, cancelled, completed)

### chat_history
- `chat_id` (PRIMARY KEY): Unique identifier for the chat
- `request_id`: Associated request ID
- `user1_id`: First participant
- `user2_id`: Second participant
- `accepted_at`: When the chat was accepted
- `completed_at`: When the chat was completed
- `duration`: Duration of the chat in seconds

### message_history
- `message_id` (PRIMARY KEY): Unique identifier for the message
- `chat_id`: Associated chat ID
- `sender_id`: User who sent the message
- `content`: Content of the message
- `has_attachment`: Whether the message has an attachment
- `sent_at`: When the message was sent

### statistics
- `user_id` (PRIMARY KEY): Discord user ID
- `chats_initiated`: Number of chats initiated
- `chats_accepted`: Number of chats accepted
- `total_chat_time`: Total time spent in chats
- `messages_sent`: Number of messages sent
- `last_updated`: When the statistics were last updated

## Technical Implementation

### Core Components

1. **Bot Core (`bot.py`)**: Main entry point and event handler
2. **Coffee Commands (`cogs/coffee_commands.py`)**: Implements the /coffee command and all button interactions
3. **Message Handler (`utils/message_handler.py`)**: Manages message relay and formatting
4. **UI Components (`utils/ui.py`)**: Defines custom UI elements like buttons and views
5. **Database Manager (`database/database.py`)**: Handles all database operations
6. **Error Handler (`cogs/error_handler.py`)**: Manages error handling and logging
7. **Web Server (`web_server.py`)**: Provides a web interface for uptime monitoring and status

### Key Technical Features

- **Dynamic UI**: Buttons and views adapt based on user's current state
- **State Management**: Robust tracking of user states to prevent conflicting actions
- **Timestamp Handling**: Consistent formatting with fallback mechanisms
- **Database Transactions**: ACID-compliant operations for data integrity
- **Error Recovery**: Graceful handling of edge cases and unexpected errors
- **Cross-Server Communication**: Seamless interaction between users on different servers
- **Asynchronous Processing**: Non-blocking operations for responsive user experience
- **Production-Ready Web Server**: Uses Waitress WSGI server for reliable web service

## Hosting Options

### Self-Hosting

1. Ensure you have Python 3.8+ installed
2. Install dependencies with `pip install -r requirements.txt`
3. Configure your `.env` file with the required credentials
4. Run the bot with `python bot.py`

### Hosting on Replit

1. Create a new Replit project
2. Upload all files from this repository
3. Add your Discord bot token as a secret named `DISCORD_TOKEN`
4. Click Run to start the bot
5. Set up UptimeRobot to ping the Replit URL to keep it running

### Hosting on VPS/Dedicated Server

1. Clone the repository to your server
2. Install dependencies with `pip install -r requirements.txt`
3. Configure your `.env` file
4. Set up a systemd service or use a process manager like PM2 or Supervisor
5. (Optional) Set up a reverse proxy with Nginx or Apache if you want to expose the web interface

Example systemd service file (`coffee-bot.service`):
```
[Unit]
Description=Coffee Chat Discord Bot
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/coffee_bot
ExecStart=/usr/bin/python3 /path/to/coffee_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Setup Your Own Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and add a bot
3. Enable the necessary intents (Members and Message Content)
4. Generate an invite link with the `bot` and `applications.commands` scopes
   - You can use the included `generate_oauth_url.py` script to create this link
   ```
   python generate_oauth_url.py --client-id=your_client_id_here
   ```
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
- For full details, see our [Privacy Policy](docs/privacy.html)
- By using the bot, users agree to our [Terms of Service](docs/terms.html)

## Security Measures

- User interactions are validated before processing
- Credentials are managed via environment variables
- OAuth with restricted permissions
- Input sanitization for all user-provided content
- Rate limiting to prevent abuse
- Secure database transactions
- Production-ready WSGI server (Waitress) for web interface

## Future Enhancements

- Rating system for coffee chats
- More detailed statistics and analytics
- Scheduled coffee chats
- Topic-based matching
- AI-powered conversation starters
- Integration with other platforms
- Customizable chat duration limits
- Server-specific configuration options
- Advanced matching algorithms
- Internationalization support

## Troubleshooting

### Common Issues

1. **Bot not responding to commands**
   - Ensure the bot has proper permissions
   - Check if the bot is online
   - Verify slash commands are registered

2. **Database errors**
   - Check file permissions for the SQLite database
   - Ensure no other process is locking the database
   - Verify the database schema is up to date

3. **Message relay issues**
   - Verify the bot can send DMs to users
   - Check if users have DMs enabled
   - Ensure the bot has the necessary permissions

4. **Web server issues**
   - Check if port 8080 is available and not blocked by a firewall
   - Verify Waitress is installed correctly
   - Check network configuration if hosting behind NAT

### Debugging

The bot uses Python's logging module with different log levels:
- INFO: General operational information
- WARNING: Potential issues that don't affect functionality
- ERROR: Problems that affect functionality
- DEBUG: Detailed information for troubleshooting

To enable more detailed logging, modify the logging level in `bot.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

### Code Style

This project follows PEP 8 guidelines with the following exceptions:
- Line length limit of 100 characters
- Use of double quotes for strings

## Requirements

- Python 3.8 or higher
- discord.py 2.0 or higher
- aiosqlite for database management
- python-dotenv for environment variables
- flask for web interface
- waitress for production-ready web server
- PyNaCl for interaction verification
- requests for API calls

## Additional Files

- `generate_oauth_url.py` - Script to generate OAuth2 URLs with the correct permissions
- `interactions_endpoint.py` - Flask server for handling Discord interactions via HTTP
- `docs/` - Directory containing HTML documentation, privacy policy, and terms of service
- `web_server.py` - Production-ready web server for uptime monitoring
- `start_coffee_bot.ps1` - PowerShell script for easy startup on Windows
- `create_shortcut.ps1` - Script to create a desktop shortcut on Windows

## Architecture

```
coffee_bot/
├── bot.py                 # Main entry point
├── web_server.py          # Web server for uptime monitoring
├── requirements.txt       # Dependencies
├── .env                   # Environment variables (create from .env.sample)
├── .env.sample            # Sample environment variables
├── cogs/                  # Discord.py cogs
│   ├── __init__.py
│   ├── coffee_commands.py # Main command implementation
│   ├── error_handler.py   # Error handling
│   └── message_handler_cog.py # Message relay cog
├── database/              # Database management
│   ├── __init__.py
│   ├── database.py        # Core database functions
│   └── schema.py          # Database schema
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── message_handler.py # Message formatting and relay
│   ├── ui.py              # UI components
│   └── status_updater.py  # Bot status management
└── docs/                  # Documentation
    ├── privacy.html       # Privacy policy
    ├── terms.html         # Terms of service
    └── index.html         # Documentation home
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Discord.py team for the excellent library
- All contributors who have helped improve this bot
- The Discord community for feedback and support
- Waitress team for the production-ready WSGI server
