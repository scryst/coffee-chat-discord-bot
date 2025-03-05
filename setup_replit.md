# Setting Up Your Coffee Chat Bot on Replit

Follow these steps to host your Coffee Chat Bot on Replit so you don't have to keep it running on your local machine.

## Step 1: Create a Replit Account

1. Go to [Replit](https://replit.com/) and sign up for an account if you don't have one already.

## Step 2: Create a New Repl

1. Click the "+" button to create a new repl
2. Select "Import from GitHub" 
3. If you have your code on GitHub, enter your repository URL
4. Alternatively, select "Python" as the language and create a blank repl

## Step 3: Upload Your Files

If you created a blank repl:

1. Upload all the files from your local `coffee_bot` folder to the repl
   - `bot.py`
   - `database.py`
   - `keep_alive.py`
   - `requirements.txt`
   - `.replit`
   - `replit.nix`

## Step 4: Set Up Environment Variables

1. In your repl, click on the "Secrets" tool in the left sidebar (lock icon)
2. Add a new secret:
   - Key: `DISCORD_TOKEN`
   - Value: Your Discord bot token

## Step 5: Run the Bot

1. Click the "Run" button at the top of the screen
2. The console should show the bot connecting to Discord
3. Your bot should now be online in your Discord server

## Step 6: Keep the Bot Running 24/7

By default, Replit will shut down your bot after a period of inactivity. To keep it running:

1. Sign up for a free account on [UptimeRobot](https://uptimerobot.com/)
2. Create a new monitor:
   - Monitor Type: HTTP(s)
   - Friendly Name: Coffee Chat Bot
   - URL: Copy the URL from your Replit webview (looks like `https://your-repl-name.your-username.repl.co`)
   - Monitoring Interval: Every 5 minutes

This will ping your bot every 5 minutes, keeping it active.

## Troubleshooting

- If the bot doesn't connect, check that your Discord token is correct in the Secrets
- Make sure all required packages are in your `requirements.txt` file
- Check the console for any error messages
- If the bot goes offline, make sure UptimeRobot is properly configured

## Updating Your Bot

To update your bot:
1. Make changes to the code in Replit's editor
2. Click "Run" to restart the bot with the new changes

Alternatively, you can update your local code and then upload the changed files to Replit.
