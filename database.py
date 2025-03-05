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
            avatar_url TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create servers table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            server_id INTEGER PRIMARY KEY,
            server_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create user_servers junction table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS user_servers (
            user_id INTEGER,
            server_id INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, server_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (server_id) REFERENCES servers(server_id)
        )
        ''')
        
        # Create coffee chat requests table with topics
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS coffee_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            server_id INTEGER,
            topic TEXT,
            description TEXT,
            is_public BOOLEAN DEFAULT 1,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (server_id) REFERENCES servers(server_id)
        )
        ''')
        
        # Create active chats table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS active_chats (
            chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER,
            accepter_id INTEGER,
            request_id INTEGER,
            server_id INTEGER,
            status TEXT DEFAULT 'active',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (requester_id) REFERENCES users(user_id),
            FOREIGN KEY (accepter_id) REFERENCES users(user_id),
            FOREIGN KEY (request_id) REFERENCES coffee_requests(request_id),
            FOREIGN KEY (server_id) REFERENCES servers(server_id)
        )
        ''')
        
        # Create chat history table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER,
            accepter_id INTEGER,
            server_id INTEGER,
            topic TEXT,
            duration INTEGER,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (requester_id) REFERENCES users(user_id),
            FOREIGN KEY (accepter_id) REFERENCES users(user_id),
            FOREIGN KEY (server_id) REFERENCES servers(server_id)
        )
        ''')
        
        # Create messages table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            sender_id INTEGER,
            content TEXT,
            has_attachment BOOLEAN DEFAULT 0,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES active_chats(chat_id),
            FOREIGN KEY (sender_id) REFERENCES users(user_id)
        )
        ''')
        
        await self.conn.commit()
    
    # User Management
    async def register_user(self, user_id, username, avatar_url=None):
        """Register or update a user in the database"""
        if not self.conn:
            await self.setup()
        
        await self.conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, avatar_url) VALUES (?, ?, ?)",
            (user_id, username, avatar_url)
        )
        await self.conn.commit()
    
    async def register_server(self, server_id, server_name):
        """Register or update a server in the database"""
        if not self.conn:
            await self.setup()
        
        await self.conn.execute(
            "INSERT OR REPLACE INTO servers (server_id, server_name) VALUES (?, ?)",
            (server_id, server_name)
        )
        await self.conn.commit()
    
    async def add_user_to_server(self, user_id, server_id):
        """Add a user to a server in the database"""
        if not self.conn:
            await self.setup()
        
        await self.conn.execute(
            "INSERT OR IGNORE INTO user_servers (user_id, server_id) VALUES (?, ?)",
            (user_id, server_id)
        )
        await self.conn.commit()
    
    # Coffee Request Management
    async def create_coffee_request(self, user_id, server_id, topic, description, is_public=True):
        """Create a new coffee chat request with topic and description"""
        if not self.conn:
            await self.setup()
        
        # Check if user already has an active request
        async with self.conn.execute(
            "SELECT request_id FROM coffee_requests WHERE user_id = ? AND status = 'open'",
            (user_id,)
        ) as cursor:
            if await cursor.fetchone():
                return None  # Request already exists
        
        # Check if user is in an active chat
        if await self.is_in_chat(user_id):
            return None  # User already in a chat
        
        # Create the request
        cursor = await self.conn.execute(
            "INSERT INTO coffee_requests (user_id, server_id, topic, description, is_public) VALUES (?, ?, ?, ?, ?)",
            (user_id, server_id, topic, description, is_public)
        )
        request_id = cursor.lastrowid
        await self.conn.commit()
        return request_id
    
    async def cancel_coffee_request(self, request_id, user_id):
        """Cancel a pending coffee chat request"""
        if not self.conn:
            await self.setup()
        
        # Verify the request belongs to the user
        async with self.conn.execute(
            "SELECT 1 FROM coffee_requests WHERE request_id = ? AND user_id = ? AND status = 'open'",
            (request_id, user_id)
        ) as cursor:
            if not await cursor.fetchone():
                return False
        
        await self.conn.execute(
            "UPDATE coffee_requests SET status = 'cancelled' WHERE request_id = ?",
            (request_id,)
        )
        await self.conn.commit()
        return True
    
    async def get_user_coffee_request(self, user_id):
        """Get a user's active coffee chat request"""
        if not self.conn:
            await self.setup()
        
        async with self.conn.execute(
            """
            SELECT r.request_id, r.topic, r.description, r.is_public, r.created_at, s.server_name
            FROM coffee_requests r
            JOIN servers s ON r.server_id = s.server_id
            WHERE r.user_id = ? AND r.status = 'open'
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            return {
                "request_id": row[0],
                "topic": row[1],
                "description": row[2],
                "is_public": bool(row[3]),
                "created_at": row[4],
                "server_name": row[5]
            }
    
    async def get_all_open_requests(self, server_id=None, exclude_user_id=None):
        """Get all open coffee chat requests, optionally filtered by server"""
        if not self.conn:
            await self.setup()
        
        query = """
            SELECT 
                r.request_id, r.user_id, u.username, r.server_id, s.server_name, 
                r.topic, r.description, r.created_at, r.is_public
            FROM coffee_requests r
            JOIN users u ON r.user_id = u.user_id
            JOIN servers s ON r.server_id = s.server_id
            WHERE r.status = 'open'
        """
        params = []
        
        if server_id is not None:
            query += " AND r.server_id = ?"
            params.append(server_id)
        
        if exclude_user_id is not None:
            query += " AND r.user_id != ?"
            params.append(exclude_user_id)
        
        # Only include public requests for cross-server viewing
        if server_id is None:
            query += " AND r.is_public = 1"
        
        query += " ORDER BY r.created_at DESC"
        
        requests = []
        async with self.conn.execute(query, params) as cursor:
            async for row in cursor:
                requests.append({
                    "request_id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "server_id": row[3],
                    "server_name": row[4],
                    "topic": row[5],
                    "description": row[6],
                    "created_at": row[7],
                    "is_public": bool(row[8])
                })
        
        return requests
    
    # Chat Management
    async def create_chat(self, request_id, accepter_id):
        """Create a new coffee chat between requester and accepter"""
        if not self.conn:
            await self.setup()
        
        # Get the request details
        async with self.conn.execute(
            "SELECT user_id, server_id, topic FROM coffee_requests WHERE request_id = ? AND status = 'open'",
            (request_id,)
        ) as cursor:
            request = await cursor.fetchone()
            if not request:
                return None  # Request not found or not open
        
        requester_id, server_id, topic = request
        
        # Check if either user is already in a chat
        if await self.is_in_chat(requester_id) or await self.is_in_chat(accepter_id):
            return None  # One of the users is already in a chat
        
        # Mark the request as accepted
        await self.conn.execute(
            "UPDATE coffee_requests SET status = 'accepted' WHERE request_id = ?",
            (request_id,)
        )
        
        # Create the chat
        cursor = await self.conn.execute(
            """
            INSERT INTO active_chats 
            (requester_id, accepter_id, request_id, server_id) 
            VALUES (?, ?, ?, ?)
            """,
            (requester_id, accepter_id, request_id, server_id)
        )
        chat_id = cursor.lastrowid
        await self.conn.commit()
        
        return {
            "chat_id": chat_id,
            "requester_id": requester_id,
            "accepter_id": accepter_id,
            "server_id": server_id,
            "topic": topic
        }
    
    async def end_chat(self, user_id):
        """End an active coffee chat"""
        if not self.conn:
            await self.setup()
        
        # Find the active chat
        async with self.conn.execute(
            """
            SELECT 
                c.chat_id, c.requester_id, c.accepter_id, c.server_id, 
                c.started_at, r.topic
            FROM active_chats c
            LEFT JOIN coffee_requests r ON c.request_id = r.request_id
            WHERE (c.requester_id = ? OR c.accepter_id = ?) AND c.status = 'active'
            """,
            (user_id, user_id)
        ) as cursor:
            chat = await cursor.fetchone()
            
            if not chat:
                return None  # No active chat found
            
            chat_id, requester_id, accepter_id, server_id, started_at, topic = chat
            
            # Update the chat status
            now = datetime.datetime.now(datetime.timezone.utc)
            await self.conn.execute(
                "UPDATE active_chats SET status = 'ended', ended_at = ? WHERE chat_id = ?",
                (now, chat_id)
            )
            
            # Calculate duration in seconds
            started_at_dt = datetime.datetime.fromisoformat(str(started_at).replace('Z', '+00:00'))
            started_at_dt = started_at_dt.replace(tzinfo=datetime.timezone.utc)
            duration = int((now - started_at_dt).total_seconds())
            
            # Add to chat history
            await self.conn.execute(
                """
                INSERT INTO chat_history 
                (requester_id, accepter_id, server_id, topic, duration, started_at, ended_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (requester_id, accepter_id, server_id, topic, duration, started_at, now)
            )
            
            await self.conn.commit()
            
            return {
                "chat_id": chat_id,
                "requester_id": requester_id,
                "accepter_id": accepter_id,
                "duration": duration,
                "topic": topic
            }
    
    async def is_in_chat(self, user_id):
        """Check if a user is in an active chat"""
        if not self.conn:
            await self.setup()
        
        async with self.conn.execute(
            "SELECT 1 FROM active_chats WHERE (requester_id = ? OR accepter_id = ?) AND status = 'active'",
            (user_id, user_id)
        ) as cursor:
            return await cursor.fetchone() is not None
    
    async def get_active_chat(self, user_id):
        """Get details of a user's active chat"""
        if not self.conn:
            await self.setup()
        
        async with self.conn.execute(
            """
            SELECT 
                c.chat_id, c.requester_id, c.accepter_id, c.started_at, 
                r.topic, r.description
            FROM active_chats c
            LEFT JOIN coffee_requests r ON c.request_id = r.request_id
            WHERE (c.requester_id = ? OR c.accepter_id = ?) AND c.status = 'active'
            """,
            (user_id, user_id)
        ) as cursor:
            chat = await cursor.fetchone()
            
            if not chat:
                return None
            
            chat_id, requester_id, accepter_id, started_at, topic, description = chat
            other_user_id = accepter_id if user_id == requester_id else requester_id
            
            # Get the other user's username
            async with self.conn.execute(
                "SELECT username FROM users WHERE user_id = ?",
                (other_user_id,)
            ) as cursor2:
                username_row = await cursor2.fetchone()
                other_username = username_row[0] if username_row else "Unknown User"
            
            return {
                "chat_id": chat_id,
                "other_user_id": other_user_id,
                "other_username": other_username,
                "started_at": started_at,
                "topic": topic,
                "description": description,
                "is_requester": user_id == requester_id
            }
    
    # Message Management
    async def store_message(self, chat_id, sender_id, content, has_attachment=False):
        """Store a message in the database"""
        if not self.conn:
            await self.setup()
        
        cursor = await self.conn.execute(
            "INSERT INTO messages (chat_id, sender_id, content, has_attachment) VALUES (?, ?, ?, ?)",
            (chat_id, sender_id, content, has_attachment)
        )
        message_id = cursor.lastrowid
        await self.conn.commit()
        return message_id
    
    # Statistics
    async def get_user_stats(self, user_id):
        """Get comprehensive coffee chat statistics for a user"""
        if not self.conn:
            await self.setup()
        
        # Get total chats and duration
        async with self.conn.execute(
            """
            SELECT 
                COUNT(*), 
                SUM(duration), 
                MAX(duration),
                MIN(duration),
                AVG(duration)
            FROM chat_history 
            WHERE requester_id = ? OR accepter_id = ?
            """,
            (user_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            
            if not row or row[0] == 0:
                return {
                    "total_chats": 0,
                    "total_duration": 0,
                    "max_duration": 0,
                    "min_duration": 0,
                    "avg_duration": 0,
                    "chats_initiated": 0,
                    "chats_accepted": 0,
                    "unique_partners": 0
                }
            
            total_chats = row[0]
            total_duration = row[1] or 0
            max_duration = row[2] or 0
            min_duration = row[3] or 0
            avg_duration = row[4] or 0
        
        # Get chats initiated
        async with self.conn.execute(
            "SELECT COUNT(*) FROM chat_history WHERE requester_id = ?",
            (user_id,)
        ) as cursor:
            chats_initiated = (await cursor.fetchone())[0]
        
        # Get chats accepted
        async with self.conn.execute(
            "SELECT COUNT(*) FROM chat_history WHERE accepter_id = ?",
            (user_id,)
        ) as cursor:
            chats_accepted = (await cursor.fetchone())[0]
        
        # Get unique partners
        async with self.conn.execute(
            """
            SELECT COUNT(DISTINCT 
                CASE 
                    WHEN requester_id = ? THEN accepter_id 
                    ELSE requester_id 
                END
            ) 
            FROM chat_history 
            WHERE requester_id = ? OR accepter_id = ?
            """,
            (user_id, user_id, user_id)
        ) as cursor:
            unique_partners = (await cursor.fetchone())[0]
        
        return {
            "total_chats": total_chats,
            "total_duration": total_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
            "avg_duration": avg_duration,
            "chats_initiated": chats_initiated,
            "chats_accepted": chats_accepted,
            "unique_partners": unique_partners
        }
    
    async def get_leaderboard(self, server_id=None, limit=10):
        """Get the leaderboard of users by number of chats and total time"""
        if not self.conn:
            await self.setup()
        
        query = """
            SELECT 
                u.user_id, 
                u.username, 
                COUNT(DISTINCT h.history_id) as chat_count,
                SUM(h.duration) as total_duration
            FROM users u
            LEFT JOIN (
                SELECT history_id, requester_id as user_id, duration FROM chat_history
                UNION ALL
                SELECT history_id, accepter_id as user_id, duration FROM chat_history
            ) h ON u.user_id = h.user_id
        """
        
        params = []
        
        if server_id is not None:
            query += " LEFT JOIN user_servers us ON u.user_id = us.user_id WHERE us.server_id = ?"
            params.append(server_id)
        
        query += """
            GROUP BY u.user_id
            ORDER BY chat_count DESC, total_duration DESC
            LIMIT ?
        """
        params.append(limit)
        
        leaderboard = []
        async with self.conn.execute(query, params) as cursor:
            async for row in cursor:
                leaderboard.append({
                    "user_id": row[0],
                    "username": row[1],
                    "chat_count": row[2],
                    "total_duration": row[3] or 0
                })
        
        return leaderboard
    
    async def close(self):
        """Close the database connection"""
        if self.conn:
            await self.conn.close()
            self.conn = None
