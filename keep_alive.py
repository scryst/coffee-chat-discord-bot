from flask import Flask
from threading import Thread
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('keep_alive')

app = Flask('')

@app.route('/')
def home():
    return "Coffee Chat Bot is running!"

def run():
    try:
        app.run(host='0.0.0.0', port=8080)
        logger.info("Keep alive server started")
    except Exception as e:
        logger.error(f"Error starting keep alive server: {e}")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    logger.info("Keep alive thread started")
    return t
