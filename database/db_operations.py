import aiosqlite
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('coffee_bot.database')

DB_PATH = Path('coffee_bot.db')

# User operations
async def get_or_create_user(user_id, username, discriminator=None):
    """Get a user from the database or create if not exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Check if user exists
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", 
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if user:
            return dict(user)
        
        # Create new user
        await db.execute(
            "INSERT INTO users (user_id, username, discriminator) VALUES (?, ?, ?)",
            (user_id, username, discriminator)
        )
        await db.commit()
        
        # Get the newly created user
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", 
            (user_id,)
        )
        new_user = await cursor.fetchone()
        return dict(new_user)

async def get_user_stats(user_id):
    """Get statistics for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute(
            """
            SELECT 
                u.user_id, 
                u.username, 
                u.total_chats, 
                u.total_time, 
                u.rating,
                COUNT(DISTINCT ch.chat_id) as completed_chats
            FROM users u
            LEFT JOIN active_chats ac ON (u.user_id = ac.user1_id OR u.user_id = ac.user2_id)
            LEFT JOIN chat_history ch ON ac.chat_id = ch.chat_id
            WHERE u.user_id = ?
            GROUP BY u.user_id
            """,
            (user_id,)
        )
        stats = await cursor.fetchone()
        
        if stats:
            return dict(stats)
        return None

# Server operations
async def get_or_create_server(server_id, server_name):
    """Get a server from the database or create if not exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Check if server exists
        cursor = await db.execute(
            "SELECT * FROM servers WHERE server_id = ?", 
            (server_id,)
        )
        server = await cursor.fetchone()
        
        if server:
            return dict(server)
        
        # Create new server
        await db.execute(
            "INSERT INTO servers (server_id, server_name) VALUES (?, ?)",
            (server_id, server_name)
        )
        await db.commit()
        
        # Get the newly created server
        cursor = await db.execute(
            "SELECT * FROM servers WHERE server_id = ?", 
            (server_id,)
        )
        new_server = await cursor.fetchone()
        return dict(new_server)

# Chat request operations
async def create_chat_request(user_id, server_id, topic, description):
    """Create a new chat request."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Create request
        cursor = await db.execute(
            """
            INSERT INTO chat_requests 
                (user_id, server_id, topic, description) 
            VALUES (?, ?, ?, ?)
            """,
            (user_id, server_id, topic, description)
        )
        request_id = cursor.lastrowid
        await db.commit()
        
        # Get the created request
        cursor = await db.execute(
            "SELECT * FROM chat_requests WHERE request_id = ?", 
            (request_id,)
        )
        request = await cursor.fetchone()
        return dict(request)

async def get_pending_requests(exclude_user_id=None):
    """Get all pending chat requests, optionally excluding a user's own requests."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        query = """
        SELECT 
            cr.*, 
            u.username as requester_name,
            s.server_name
        FROM chat_requests cr
        JOIN users u ON cr.user_id = u.user_id
        JOIN servers s ON cr.server_id = s.server_id
        WHERE cr.status = 'pending'
        """
        
        params = []
        if exclude_user_id:
            query += " AND cr.user_id != ?"
            params.append(exclude_user_id)
        
        cursor = await db.execute(query, params)
        requests = await cursor.fetchall()
        return [dict(r) for r in requests]

async def get_user_request(user_id):
    """Get a user's pending chat request if any."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute(
            """
            SELECT * FROM chat_requests 
            WHERE user_id = ? AND status = 'pending'
            """,
            (user_id,)
        )
        request = await cursor.fetchone()
        
        if request:
            return dict(request)
        return None

async def cancel_request(request_id):
    """Cancel a chat request."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE chat_requests SET status = 'cancelled' WHERE request_id = ?",
            (request_id,)
        )
        await db.commit()
        return True

# Chat operations
async def create_chat(request_id, user1_id, user2_id):
    """Create a new active chat."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Update request status
        await db.execute(
            "UPDATE chat_requests SET status = 'accepted' WHERE request_id = ?",
            (request_id,)
        )
        
        # Create active chat
        cursor = await db.execute(
            """
            INSERT INTO active_chats 
                (request_id, user1_id, user2_id) 
            VALUES (?, ?, ?)
            """,
            (request_id, user1_id, user2_id)
        )
        chat_id = cursor.lastrowid
        await db.commit()
        
        # Get the created chat
        cursor = await db.execute(
            """
            SELECT 
                ac.*, 
                cr.topic, 
                cr.description,
                u1.username as user1_name,
                u2.username as user2_name
            FROM active_chats ac
            JOIN chat_requests cr ON ac.request_id = cr.request_id
            JOIN users u1 ON ac.user1_id = u1.user_id
            JOIN users u2 ON ac.user2_id = u2.user_id
            WHERE ac.chat_id = ?
            """, 
            (chat_id,)
        )
        chat = await cursor.fetchone()
        return dict(chat)

async def get_active_chat(user_id):
    """Get a user's active chat if any."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute(
            """
            SELECT 
                ac.*, 
                cr.topic, 
                cr.description,
                u1.username as user1_name,
                u2.username as user2_name
            FROM active_chats ac
            JOIN chat_requests cr ON ac.request_id = cr.request_id
            JOIN users u1 ON ac.user1_id = u1.user_id
            JOIN users u2 ON ac.user2_id = u2.user_id
            WHERE (ac.user1_id = ? OR ac.user2_id = ?) AND ac.status = 'active'
            """,
            (user_id, user_id)
        )
        chat = await cursor.fetchone()
        
        if chat:
            return dict(chat)
        return None

async def end_chat(chat_id, duration=None):
    """End an active chat and record history."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Update chat status
        await db.execute(
            "UPDATE active_chats SET status = 'ended' WHERE chat_id = ?",
            (chat_id,)
        )
        
        # Create chat history entry
        await db.execute(
            """
            INSERT INTO chat_history 
                (chat_id, ended_at, duration) 
            VALUES (?, ?, ?)
            """,
            (chat_id, datetime.now().isoformat(), duration)
        )
        
        # Update user stats
        if duration:
            chat = await db.execute(
                "SELECT user1_id, user2_id FROM active_chats WHERE chat_id = ?",
                (chat_id,)
            )
            chat_data = await chat.fetchone()
            
            if chat_data:
                user1_id, user2_id = chat_data
                
                await db.execute(
                    """
                    UPDATE users 
                    SET total_chats = total_chats + 1, total_time = total_time + ? 
                    WHERE user_id IN (?, ?)
                    """,
                    (duration, user1_id, user2_id)
                )
        
        await db.commit()
        return True

# Message operations
async def save_message(chat_id, sender_id, content, has_attachment=False):
    """Save a message to the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO messages 
                (chat_id, sender_id, content, has_attachment) 
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, sender_id, content, has_attachment)
        )
        message_id = cursor.lastrowid
        await db.commit()
        return message_id

# Leaderboard operations
async def get_leaderboard(limit=10):
    """Get the coffee chat leaderboard."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute(
            """
            SELECT 
                user_id, 
                username, 
                total_chats, 
                total_time, 
                rating
            FROM users
            WHERE total_chats > 0
            ORDER BY total_chats DESC, total_time DESC
            LIMIT ?
            """,
            (limit,)
        )
        leaderboard = await cursor.fetchall()
        return [dict(entry) for entry in leaderboard]
