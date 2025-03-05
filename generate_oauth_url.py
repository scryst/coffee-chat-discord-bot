import os
from dotenv import load_dotenv
import argparse

def calculate_permissions_integer():
    """
    Calculate the permissions integer for the bot.
    
    This includes the following permissions:
    - VIEW_CHANNEL (1 << 10) = 1024
    - SEND_MESSAGES (1 << 11) = 2048
    - EMBED_LINKS (1 << 14) = 16384
    - ATTACH_FILES (1 << 15) = 32768
    - READ_MESSAGE_HISTORY (1 << 16) = 65536
    - USE_APPLICATION_COMMANDS (1 << 31) = 2147483648
    
    Total: 2147601408
    """
    permissions = 0
    permissions |= (1 << 10)  # VIEW_CHANNEL
    permissions |= (1 << 11)  # SEND_MESSAGES
    permissions |= (1 << 14)  # EMBED_LINKS
    permissions |= (1 << 15)  # ATTACH_FILES
    permissions |= (1 << 16)  # READ_MESSAGE_HISTORY
    permissions |= (1 << 31)  # USE_APPLICATION_COMMANDS
    
    return permissions

def generate_oauth_url(client_id=None, permissions=None):
    """Generate an OAuth2 URL for the bot with the specified permissions."""
    # Load environment variables if client_id is not provided
    if client_id is None:
        load_dotenv()
        client_id = os.getenv('DISCORD_CLIENT_ID')
        
        if not client_id:
            print("Error: DISCORD_CLIENT_ID not found in .env file.")
            print("Please provide a client ID using the --client-id argument or add it to your .env file.")
            return None
    
    # Calculate permissions if not provided
    if permissions is None:
        permissions = calculate_permissions_integer()
    
    # Generate the OAuth URL
    oauth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={client_id}"
        f"&permissions={permissions}"
        f"&scope=bot%20applications.commands"
    )
    
    return oauth_url

def main():
    parser = argparse.ArgumentParser(description='Generate an OAuth2 URL for your Discord bot.')
    parser.add_argument('--client-id', help='Your Discord application client ID')
    parser.add_argument('--permissions', type=int, help='Permissions integer (default: 2147601408)')
    
    args = parser.parse_args()
    
    oauth_url = generate_oauth_url(args.client_id, args.permissions)
    
    if oauth_url:
        print("\n=== Coffee Chat Bot OAuth2 URL ===")
        print(oauth_url)
        print("\nThis URL includes the following permissions:")
        print("- View Channels")
        print("- Send Messages")
        print("- Embed Links")
        print("- Attach Files")
        print("- Read Message History")
        print("- Use Application Commands")
        print("\nAnd the following scopes:")
        print("- bot")
        print("- applications.commands")
        print("\nShare this URL to invite the bot to a server.")

if __name__ == "__main__":
    main()
