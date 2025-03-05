import aiosqlite
import logging
import os
from pathlib import Path

logger = logging.getLogger('coffee_bot.database')

DB_PATH = Path('coffee_bot.db')

async def create_tables():
    """Create all necessary database tables if they don't exist."""
    logger.info("Setting up database tables")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            discriminator TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_chats INTEGER DEFAULT 0,
            total_time INTEGER DEFAULT 0,
            rating REAL DEFAULT 0
        )
        ''')
        
        # Servers table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            server_id INTEGER PRIMARY KEY,
            server_name TEXT NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Requests table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS chat_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            server_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            message_id INTEGER,
            channel_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (server_id) REFERENCES servers (server_id)
        )
        ''')
        
        # Active chats table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS active_chats (
            chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (request_id) REFERENCES chat_requests (request_id),
            FOREIGN KEY (user1_id) REFERENCES users (user_id),
            FOREIGN KEY (user2_id) REFERENCES users (user_id)
        )
        ''')
        
        # Chat history table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            chat_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            ended_at TIMESTAMP,
            duration INTEGER,
            user1_rating INTEGER,
            user2_rating INTEGER,
            FOREIGN KEY (chat_id) REFERENCES active_chats (chat_id)
        )
        ''')
        
        # Messages table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            content TEXT,
            has_attachment BOOLEAN DEFAULT FALSE,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES active_chats (chat_id),
            FOREIGN KEY (sender_id) REFERENCES users (user_id)
        )
        ''')
        
        await db.commit()
        logger.info("Database tables created successfully")

async def initialize_database():
    """Initialize the database and create tables."""
    logger.info(f"Initializing database at {DB_PATH}")
    await create_tables()
    logger.info("Database initialization complete")
