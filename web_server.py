from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Coffee Chat Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Create and start a web server thread to keep the bot alive on Replit."""
    t = Thread(target=run)
    t.start()
