from flask import Flask
from threading import Thread
import waitress
import logging

app = Flask(__name__)
logger = logging.getLogger('coffee_bot.web_server')

@app.route('/')
def home():
    return "Coffee Chat Bot is running!"

def run():
    # Use waitress instead of Flask's development server
    logger.info("Starting web server with Waitress on 0.0.0.0:8080")
    waitress.serve(app, host='0.0.0.0', port=8080, threads=4)

def keep_alive():
    """Create and start a web server thread to keep the bot alive."""
    t = Thread(target=run)
    t.daemon = True  # Daemon thread will close when main program exits
    t.start()
