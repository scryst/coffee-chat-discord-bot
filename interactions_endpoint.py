import os
import json
import logging
import nacl.signing
import nacl.exceptions
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('interactions_endpoint')

# Load environment variables
load_dotenv()
PUBLIC_KEY = os.getenv('DISCORD_PUBLIC_KEY')

app = Flask(__name__)

def verify_signature(request):
    """Verify that the request came from Discord."""
    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')
    
    if not signature or not timestamp:
        logger.warning("Missing signature or timestamp headers")
        return False
    
    if not PUBLIC_KEY:
        logger.error("DISCORD_PUBLIC_KEY not found in environment variables")
        return False
    
    try:
        body = request.data.decode('utf-8')
        verify_key = nacl.signing.VerifyKey(bytes.fromhex(PUBLIC_KEY))
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        return True
    except nacl.exceptions.BadSignatureError:
        logger.warning("Invalid request signature")
        return False
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False

@app.route('/interactions', methods=['POST'])
def interactions():
    """Handle Discord interactions."""
    # Verify the request signature
    if not verify_signature(request):
        return 'Invalid request signature', 401
    
    # Parse the request body
    try:
        interaction = request.json
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
        return 'Invalid request body', 400
    
    # Handle ping type (required for Discord to verify the endpoint)
    if interaction.get('type') == 1:
        logger.info("Received PING interaction, responding with PONG")
        return jsonify({'type': 1})
    
    # For other interaction types, respond with a message that the bot is in gateway mode
    logger.info(f"Received interaction of type {interaction.get('type')}")
    return jsonify({
        'type': 4,  # CHANNEL_MESSAGE_WITH_SOURCE
        'data': {
            'content': 'This bot is currently running in gateway mode and does not support HTTP interactions. Please use the slash commands directly in Discord.'
        }
    })

def run_interactions_server(host='0.0.0.0', port=8080):
    """Run the interactions endpoint server."""
    app.run(host=host, port=port)

if __name__ == '__main__':
    logger.info("Starting interactions endpoint server")
    run_interactions_server()
