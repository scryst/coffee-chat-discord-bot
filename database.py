import aiosqlite
import datetime

class Database:
    def __init__(self, db_path="coffee_chat.db"):
        self.db_path = db_path
        self.conn = None
    
    async def setup(self):
        """Initialize the database connection and create tables if they don't exist"""
        self.conn = await aiosqlite.connect(self.db_path)
        
        # Create users table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            guild_id INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create active requests table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            guild_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, guild_id)
        )
        ''')
        
        # Create active calls table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            call_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            guild_id INTEGER,
            status TEXT DEFAULT 'active',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        )
        ''')
        
        # Create call history table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS call_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            guild_id INTEGER,
            duration INTEGER,
            started_at TIMESTAMP,
            ended_at TIMESTAMP
        )
        ''')
        
        await self.conn.commit()
    
    async def register_user(self, user_id, username, guild_id):
        """Register a user in the database"""
        if not self.conn:
            await self.setup()
        
        await self.conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, guild_id) VALUES (?, ?, ?)",
            (user_id, username, guild_id)
        )
        await self.conn.commit()
    
    async def create_request(self, user_id, guild_id):
        """Create a new coffee chat request"""
        if not self.conn:
            await self.setup()
        
        # First check if user already has an active request
        async with self.conn.execute(
            "SELECT request_id FROM requests WHERE user_id = ? AND guild_id = ? AND status = 'pending'",
            (user_id, guild_id)
        ) as cursor:
            if await cursor.fetchone():
                return False  # Request already exists
        
        # Check if user is in an active call
        if await self.is_in_call(user_id):
            return False  # User already in a call
        
        # Create the request
        await self.conn.execute(
            "INSERT OR REPLACE INTO requests (user_id, guild_id, status) VALUES (?, ?, 'pending')",
            (user_id, guild_id)
        )
        await self.conn.commit()
        return True
    
    async def cancel_request(self, user_id, guild_id):
        """Cancel a pending coffee chat request"""
        if not self.conn:
            await self.setup()
        
        await self.conn.execute(
            "DELETE FROM requests WHERE user_id = ? AND guild_id = ? AND status = 'pending'",
            (user_id, guild_id)
        )
        await self.conn.commit()
    
    async def get_pending_requests(self, guild_id, exclude_user_id=None):
        """Get all pending coffee chat requests for a guild"""
        if not self.conn:
            await self.setup()
        
        query = "SELECT r.request_id, r.user_id, u.username, r.created_at FROM requests r JOIN users u ON r.user_id = u.user_id WHERE r.guild_id = ? AND r.status = 'pending'"
        params = [guild_id]
        
        if exclude_user_id:
            query += " AND r.user_id != ?"
            params.append(exclude_user_id)
        
        requests = []
        async with self.conn.execute(query, params) as cursor:
            async for row in cursor:
                requests.append({
                    "request_id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "created_at": row[3]
                })
        
        return requests
    
    async def has_pending_request(self, user_id, guild_id):
        """Check if a user has a pending coffee chat request"""
        if not self.conn:
            await self.setup()
        
        async with self.conn.execute(
            "SELECT 1 FROM requests WHERE user_id = ? AND guild_id = ? AND status = 'pending'",
            (user_id, guild_id)
        ) as cursor:
            return await cursor.fetchone() is not None
    
    async def create_call(self, user1_id, user2_id, guild_id):
        """Create a new coffee chat call between two users"""
        if not self.conn:
            await self.setup()
        
        # Remove any pending requests from both users
        await self.conn.execute(
            "DELETE FROM requests WHERE (user_id = ? OR user_id = ?) AND guild_id = ?",
            (user1_id, user2_id, guild_id)
        )
        
        # Create the call
        await self.conn.execute(
            "INSERT INTO calls (user1_id, user2_id, guild_id, status) VALUES (?, ?, ?, 'active')",
            (user1_id, user2_id, guild_id)
        )
        await self.conn.commit()
    
    async def end_call(self, user_id):
        """End an active coffee chat call"""
        if not self.conn:
            await self.setup()
        
        # Find the active call
        async with self.conn.execute(
            "SELECT call_id, user1_id, user2_id, guild_id, started_at FROM calls WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'",
            (user_id, user_id)
        ) as cursor:
            call = await cursor.fetchone()
            
            if not call:
                return None  # No active call found
            
            call_id, user1_id, user2_id, guild_id, started_at = call
            
            # Update the call status
            now = datetime.datetime.now(datetime.timezone.utc)
            await self.conn.execute(
                "UPDATE calls SET status = 'ended', ended_at = ? WHERE call_id = ?",
                (now, call_id)
            )
            
            # Calculate duration in seconds
            started_at_dt = datetime.datetime.fromisoformat(str(started_at).replace('Z', '+00:00'))
            started_at_dt = started_at_dt.replace(tzinfo=datetime.timezone.utc)
            duration = int((now - started_at_dt).total_seconds())
            
            # Add to call history
            await self.conn.execute(
                "INSERT INTO call_history (user1_id, user2_id, guild_id, duration, started_at, ended_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user1_id, user2_id, guild_id, duration, started_at, now)
            )
            
            await self.conn.commit()
            
            return {
                "user1_id": user1_id,
                "user2_id": user2_id,
                "duration": duration
            }
    
    async def is_in_call(self, user_id):
        """Check if a user is in an active call"""
        if not self.conn:
            await self.setup()
        
        async with self.conn.execute(
            "SELECT 1 FROM calls WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'",
            (user_id, user_id)
        ) as cursor:
            return await cursor.fetchone() is not None
    
    async def get_active_call(self, user_id):
        """Get details of a user's active call"""
        if not self.conn:
            await self.setup()
        
        async with self.conn.execute(
            "SELECT call_id, user1_id, user2_id, started_at FROM calls WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'",
            (user_id, user_id)
        ) as cursor:
            call = await cursor.fetchone()
            
            if not call:
                return None
            
            call_id, user1_id, user2_id, started_at = call
            other_user_id = user2_id if user_id == user1_id else user1_id
            
            # Get the other user's username
            async with self.conn.execute(
                "SELECT username FROM users WHERE user_id = ?",
                (other_user_id,)
            ) as cursor2:
                username_row = await cursor2.fetchone()
                other_username = username_row[0] if username_row else "Unknown User"
            
            return {
                "call_id": call_id,
                "other_user_id": other_user_id,
                "other_username": other_username,
                "started_at": started_at
            }
    
    async def get_call_stats(self, user_id, guild_id=None):
        """Get call statistics for a user"""
        if not self.conn:
            await self.setup()
        
        query = "SELECT COUNT(*), SUM(duration) FROM call_history WHERE (user1_id = ? OR user2_id = ?)"
        params = [user_id, user_id]
        
        if guild_id:
            query += " AND guild_id = ?"
            params.append(guild_id)
        
        async with self.conn.execute(query, params) as cursor:
            row = await cursor.fetchone()
            
            if not row or row[0] == 0:
                return {"total_calls": 0, "total_duration": 0}
            
            return {
                "total_calls": row[0],
                "total_duration": row[1] or 0  # Handle NULL sum
            }
    
    async def close(self):
        """Close the database connection"""
        if self.conn:
            await self.conn.close()
            self.conn = None
