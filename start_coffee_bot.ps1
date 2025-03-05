# PowerShell script to start the Coffee Chat Discord bot
# Navigate to the bot directory
Set-Location -Path "C:\Users\lhamr\OneDrive\Desktop\autoxi\coffee_bot"

# Activate the Python environment (assuming you're using conda)
# If you're using a different virtual environment, adjust this command accordingly
conda activate base

# Start the bot
python bot.py

# Keep the window open after the bot stops
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
