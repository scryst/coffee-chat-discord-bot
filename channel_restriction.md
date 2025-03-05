# Channel Restriction for Coffee Chat Bot

This guide explains how to restrict your Coffee Chat bot to only work in a specific channel on your Discord server.

## Getting Your Channel ID

1. First, you need to enable Developer Mode in Discord:
   - Open Discord
   - Go to User Settings (gear icon at the bottom)
   - Navigate to "Advanced" in the left sidebar
   - Toggle on "Developer Mode"

2. Get your channel ID:
   - Right-click on the channel where you want the bot to work
   - Select "Copy ID" from the context menu
   - This will copy a long number to your clipboard (this is your channel ID)

## Setting the Channel ID in Your Bot

### Option 1: Edit the bot.py file directly (on Replit)

1. Open your Replit project
2. Open the `bot.py` file
3. Find this line near the top of the file:
   ```python
   COFFEE_CHANNEL_ID = None  # You'll replace this with your channel ID
   ```
4. Replace `None` with your channel ID (in quotes):
   ```python
   COFFEE_CHANNEL_ID = 123456789012345678  # Replace with your actual channel ID
   ```
5. Save the file and restart your bot

### Option 2: Use an Environment Variable (Recommended)

1. Open your Replit project
2. Click on the "Secrets" tool in the left sidebar (lock icon)
3. Add a new secret:
   - Key: `COFFEE_CHANNEL_ID`
   - Value: Your channel ID (just the number, no quotes)
4. Click "Add new secret"

5. Then modify your bot.py file to use this environment variable:
   ```python
   # Near the top of the file, where other environment variables are loaded
   COFFEE_CHANNEL_ID = os.getenv('COFFEE_CHANNEL_ID')
   if COFFEE_CHANNEL_ID:
       COFFEE_CHANNEL_ID = int(COFFEE_CHANNEL_ID)
   ```

## How It Works

- When users try to use any coffee chat commands outside the designated channel, they will receive a private message directing them to the correct channel
- All coffee chat commands will only function in the specified channel
- DM functionality will continue to work normally regardless of channel restrictions

## Removing the Restriction

If you want to remove the channel restriction later:
- Set `COFFEE_CHANNEL_ID = None` in the bot.py file, or
- Remove the `COFFEE_CHANNEL_ID` secret from your Replit project
