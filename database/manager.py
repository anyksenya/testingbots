import sqlite3
import os
import logging
from typing import List, Optional, Tuple, Dict, Any
import datetime

from database.models import User, Chat, UserChat, Task, WeeklyStat
import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager for SQLite database operations."""
    
    def __init__(self, db_path: str = None):
        """Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the path from config.
        """
        if db_path is None:
            # Extract the database path from the SQLite URI in config
            db_uri = config.DATABASE_PATH
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri[10:]
            else:
                db_path = 'taskbot.db'
        
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Ensure the database directory exists
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        if db_dir and db_dir != '.':
            os.makedirs(db_dir, exist_ok=True)
        
        # Initialize the database
        self._init_db()
    
    def _connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def _disconnect(self):
        """Disconnect from the SQLite database."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def _init_db(self):
        """Initialize the database with required tables if they don't exist."""
        try:
            self._connect()
            
            # Create users table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    registration_date TEXT,
                    is_active INTEGER
                )
            ''')
            
            # Create chats table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT,
                    chat_type TEXT,
                    is_active INTEGER,
                    created_at TEXT
                )
            ''')
            
            # Create user_chats table (many-to-many relationship)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_chats (
                    user_id INTEGER,
                    chat_id INTEGER,
                    joined_at TEXT,
                    is_active INTEGER,
                    PRIMARY KEY (user_id, chat_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                )
            ''')
            
            # Create tasks table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    description TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    week_number INTEGER,
                    year INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                )
            ''')
            
            # Create weekly_stats table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS weekly_stats (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    week_number INTEGER,
                    year INTEGER,
                    tasks_created INTEGER,
                    tasks_completed INTEGER,
                    tasks_canceled INTEGER,
                    completion_rate REAL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                )
            ''')
            
            self.conn.commit()
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            self._disconnect()
    
    # User operations
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        try:
            self._connect()
            self.cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = self.cursor.fetchone()
            if row:
                return User.from_row(tuple(row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
        finally:
            self._disconnect()
    
    def create_user(self, user: User) -> bool:
        """Create a new user."""
        try:
            self._connect()
            self.cursor.execute(
                """
                INSERT INTO users (user_id, username, first_name, last_name, registration_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user.user_id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    user.registration_date.isoformat() if user.registration_date else None,
                    1 if user.is_active else 0
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating user {user.user_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    def update_user(self, user: User) -> bool:
        """Update an existing user."""
        try:
            self._connect()
            self.cursor.execute(
                """
                UPDATE users
                SET username = ?, first_name = ?, last_name = ?, is_active = ?
                WHERE user_id = ?
                """,
                (
                    user.username,
                    user.first_name,
                    user.last_name,
                    1 if user.is_active else 0,
                    user.user_id
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating user {user.user_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    # Chat operations
    
    def get_chat(self, chat_id: int) -> Optional[Chat]:
        """Get a chat by ID."""
        try:
            self._connect()
            self.cursor.execute(
                "SELECT * FROM chats WHERE chat_id = ?",
                (chat_id,)
            )
            row = self.cursor.fetchone()
            if row:
                return Chat.from_row(tuple(row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting chat {chat_id}: {e}")
            return None
        finally:
            self._disconnect()
    
    def create_chat(self, chat: Chat) -> bool:
        """Create a new chat."""
        try:
            self._connect()
            self.cursor.execute(
                """
                INSERT INTO chats (chat_id, title, chat_type, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    chat.chat_id,
                    chat.title,
                    chat.chat_type,
                    1 if chat.is_active else 0,
                    chat.created_at.isoformat() if chat.created_at else None
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating chat {chat.chat_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    def update_chat(self, chat: Chat) -> bool:
        """Update an existing chat."""
        try:
            self._connect()
            self.cursor.execute(
                """
                UPDATE chats
                SET title = ?, chat_type = ?, is_active = ?
                WHERE chat_id = ?
                """,
                (
                    chat.title,
                    chat.chat_type,
                    1 if chat.is_active else 0,
                    chat.chat_id
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating chat {chat.chat_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    # User-Chat operations
    
    def get_user_chat(self, user_id: int, chat_id: int) -> Optional[UserChat]:
        """Get a user-chat association."""
        try:
            self._connect()
            self.cursor.execute(
                "SELECT * FROM user_chats WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id)
            )
            row = self.cursor.fetchone()
            if row:
                return UserChat.from_row(tuple(row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting user-chat for user {user_id} and chat {chat_id}: {e}")
            return None
        finally:
            self._disconnect()
    
    def create_user_chat(self, user_chat: UserChat) -> bool:
        """Create a new user-chat association."""
        try:
            self._connect()
            self.cursor.execute(
                """
                INSERT INTO user_chats (user_id, chat_id, joined_at, is_active)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_chat.user_id,
                    user_chat.chat_id,
                    user_chat.joined_at.isoformat() if user_chat.joined_at else None,
                    1 if user_chat.is_active else 0
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating user-chat for user {user_chat.user_id} and chat {user_chat.chat_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    def update_user_chat(self, user_chat: UserChat) -> bool:
        """Update an existing user-chat association."""
        try:
            self._connect()
            self.cursor.execute(
                """
                UPDATE user_chats
                SET is_active = ?
                WHERE user_id = ? AND chat_id = ?
                """,
                (
                    1 if user_chat.is_active else 0,
                    user_chat.user_id,
                    user_chat.chat_id
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating user-chat for user {user_chat.user_id} and chat {user_chat.chat_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    def get_user_chats(self, user_id: int) -> List[Chat]:
        """Get all chats for a user."""
        try:
            self._connect()
            self.cursor.execute(
                """
                SELECT c.* FROM chats c
                JOIN user_chats uc ON c.chat_id = uc.chat_id
                WHERE uc.user_id = ? AND uc.is_active = 1 AND c.is_active = 1
                """,
                (user_id,)
            )
            rows = self.cursor.fetchall()
            return [Chat.from_row(tuple(row)) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting chats for user {user_id}: {e}")
            return []
        finally:
            self._disconnect()
    
    def get_chat_users(self, chat_id: int) -> List[User]:
        """Get all users in a chat."""
        try:
            self._connect()
            self.cursor.execute(
                """
                SELECT u.* FROM users u
                JOIN user_chats uc ON u.user_id = uc.user_id
                WHERE uc.chat_id = ? AND uc.is_active = 1 AND u.is_active = 1
                """,
                (chat_id,)
            )
            rows = self.cursor.fetchall()
            return [User.from_row(tuple(row)) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting users for chat {chat_id}: {e}")
            return []
        finally:
            self._disconnect()
    
    # Task operations
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        try:
            self._connect()
            self.cursor.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            row = self.cursor.fetchone()
            if row:
                return Task.from_row(tuple(row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
        finally:
            self._disconnect()
    
    def get_user_tasks_in_chat(self, user_id: int, chat_id: int, week_number: Optional[int] = None, year: Optional[int] = None) -> List[Task]:
        """Get tasks for a user in a specific chat, optionally filtered by week."""
        try:
            self._connect()
            query = "SELECT * FROM tasks WHERE user_id = ? AND chat_id = ?"
            params = [user_id, chat_id]
            
            if week_number is not None and year is not None:
                query += " AND week_number = ? AND year = ?"
                params.extend([week_number, year])
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [Task.from_row(tuple(row)) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting tasks for user {user_id} in chat {chat_id}: {e}")
            return []
        finally:
            self._disconnect()
    
    def create_task(self, task: Task) -> Optional[int]:
        """Create a new task."""
        try:
            self._connect()
            self.cursor.execute(
                """
                INSERT INTO tasks (user_id, chat_id, description, status, created_at, updated_at, week_number, year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.user_id,
                    task.chat_id,
                    task.description,
                    task.status,
                    task.created_at.isoformat() if task.created_at else None,
                    task.updated_at.isoformat() if task.updated_at else None,
                    task.week_number,
                    task.year
                )
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error creating task for user {task.user_id} in chat {task.chat_id}: {e}")
            return None
        finally:
            self._disconnect()
    
    def update_task(self, task: Task) -> bool:
        """Update an existing task."""
        try:
            self._connect()
            self.cursor.execute(
                """
                UPDATE tasks
                SET description = ?, status = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (
                    task.description,
                    task.status,
                    task.updated_at.isoformat() if task.updated_at else None,
                    task.task_id
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating task {task.task_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        try:
            self._connect()
            self.cursor.execute(
                "DELETE FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    def count_user_tasks_in_chat(self, user_id: int, chat_id: int, week_number: int, year: int) -> int:
        """Count the number of tasks for a user in a specific chat and week."""
        try:
            self._connect()
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM tasks
                WHERE user_id = ? AND chat_id = ? AND week_number = ? AND year = ?
                """,
                (user_id, chat_id, week_number, year)
            )
            count = self.cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            logger.error(f"Error counting tasks for user {user_id} in chat {chat_id}: {e}")
            return 0
        finally:
            self._disconnect()
    
    # Weekly stats operations
    
    def get_weekly_stat(self, user_id: int, chat_id: int, week_number: int, year: int) -> Optional[WeeklyStat]:
        """Get weekly statistics for a user in a specific chat."""
        try:
            self._connect()
            self.cursor.execute(
                """
                SELECT * FROM weekly_stats
                WHERE user_id = ? AND chat_id = ? AND week_number = ? AND year = ?
                """,
                (user_id, chat_id, week_number, year)
            )
            row = self.cursor.fetchone()
            if row:
                return WeeklyStat.from_row(tuple(row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting weekly stats for user {user_id} in chat {chat_id}: {e}")
            return None
        finally:
            self._disconnect()
    
    def get_user_stats_history_in_chat(self, user_id: int, chat_id: int, limit: int = 10) -> List[WeeklyStat]:
        """Get historical weekly statistics for a user in a specific chat."""
        try:
            self._connect()
            self.cursor.execute(
                """
                SELECT * FROM weekly_stats
                WHERE user_id = ? AND chat_id = ?
                ORDER BY year DESC, week_number DESC
                LIMIT ?
                """,
                (user_id, chat_id, limit)
            )
            rows = self.cursor.fetchall()
            return [WeeklyStat.from_row(tuple(row)) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting stats history for user {user_id} in chat {chat_id}: {e}")
            return []
        finally:
            self._disconnect()
    
    def create_or_update_weekly_stat(self, stat: WeeklyStat) -> bool:
        """Create or update weekly statistics for a user in a specific chat."""
        try:
            self._connect()
            
            # Check if stats exist for this user, chat, week, and year
            existing_stat = self.get_weekly_stat(stat.user_id, stat.chat_id, stat.week_number, stat.year)
            
            if existing_stat:
                # Update existing stats
                self.cursor.execute(
                    """
                    UPDATE weekly_stats
                    SET tasks_created = ?, tasks_completed = ?, tasks_canceled = ?, completion_rate = ?
                    WHERE user_id = ? AND chat_id = ? AND week_number = ? AND year = ?
                    """,
                    (
                        stat.tasks_created,
                        stat.tasks_completed,
                        stat.tasks_canceled,
                        stat.completion_rate,
                        stat.user_id,
                        stat.chat_id,
                        stat.week_number,
                        stat.year
                    )
                )
            else:
                # Create new stats
                self.cursor.execute(
                    """
                    INSERT INTO weekly_stats
                    (user_id, chat_id, week_number, year, tasks_created, tasks_completed, tasks_canceled, completion_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        stat.user_id,
                        stat.chat_id,
                        stat.week_number,
                        stat.year,
                        stat.tasks_created,
                        stat.tasks_completed,
                        stat.tasks_canceled,
                        stat.completion_rate
                    )
                )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating/updating weekly stats for user {stat.user_id} in chat {stat.chat_id}: {e}")
            return False
        finally:
            self._disconnect()
    
    def generate_weekly_stats_for_chat(self, chat_id: int, week_number: int, year: int) -> List[WeeklyStat]:
        """Generate weekly statistics for all users in a specific chat for a specific week."""
        try:
            self._connect()
            
            # Get all active users in the chat
            self.cursor.execute(
                """
                SELECT u.user_id FROM users u
                JOIN user_chats uc ON u.user_id = uc.user_id
                WHERE uc.chat_id = ? AND uc.is_active = 1 AND u.is_active = 1
                """,
                (chat_id,)
            )
            user_ids = [row[0] for row in self.cursor.fetchall()]
            
            stats = []
            for user_id in user_ids:
                # Count tasks by status
                self.cursor.execute(
                    """
                    SELECT COUNT(*) FROM tasks
                    WHERE user_id = ? AND chat_id = ? AND week_number = ? AND year = ?
                    """,
                    (user_id, chat_id, week_number, year)
                )
                tasks_created = self.cursor.fetchone()[0]
                
                self.cursor.execute(
                    """
                    SELECT COUNT(*) FROM tasks
                    WHERE user_id = ? AND chat_id = ? AND week_number = ? AND year = ? AND status = 'completed'
                    """,
                    (user_id, chat_id, week_number, year)
                )
                tasks_completed = self.cursor.fetchone()[0]
                
                self.cursor.execute(
                    """
                    SELECT COUNT(*) FROM tasks
                    WHERE user_id = ? AND chat_id = ? AND week_number = ? AND year = ? AND status = 'canceled'
                    """,
                    (user_id, chat_id, week_number, year)
                )
                tasks_canceled = self.cursor.fetchone()[0]
                
                # Calculate completion rate
                completion_rate = 0.0
                if tasks_created > 0:
                    completion_rate = tasks_completed / tasks_created
                
                # Create stats object
                stat = WeeklyStat(
                    user_id=user_id,
                    chat_id=chat_id,
                    week_number=week_number,
                    year=year,
                    tasks_created=tasks_created,
                    tasks_completed=tasks_completed,
                    tasks_canceled=tasks_canceled,
                    completion_rate=completion_rate
                )
                
                # Save to database
                self.create_or_update_weekly_stat(stat)
                stats.append(stat)
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error generating weekly stats for chat {chat_id}: {e}")
            return []
        finally:
            self._disconnect()
    
    def generate_weekly_stats_for_all_chats(self, week_number: int, year: int) -> Dict[int, List[WeeklyStat]]:
        """Generate weekly statistics for all users in all active chats for a specific week."""
        try:
            self._connect()
            
            # Get all active chats
            self.cursor.execute("SELECT chat_id FROM chats WHERE is_active = 1")
            chat_ids = [row[0] for row in self.cursor.fetchall()]
            
            results = {}
            for chat_id in chat_ids:
                stats = self.generate_weekly_stats_for_chat(chat_id, week_number, year)
                results[chat_id] = stats
            
            return results
        except sqlite3.Error as e:
            logger.error(f"Error generating weekly stats for all chats: {e}")
            return {}
        finally:
            self._disconnect()
    
    # Registration and initialization
    
    def register_user_in_chat(self, user: User, chat: Chat) -> bool:
        """Register a user in a chat, creating user, chat, and association if they don't exist."""
        try:
            # Create user directly
            self._connect()
            logger.info(f"Registering user {user.user_id} in chat {chat.chat_id}")
            
            # Check if user exists
            self.cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user.user_id,)
            )
            existing_user = self.cursor.fetchone()
            
            if not existing_user:
                # Create user
                logger.info(f"Creating new user {user.user_id}")
                self.cursor.execute(
                    """
                    INSERT INTO users (user_id, username, first_name, last_name, registration_date, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user.user_id,
                        user.username,
                        user.first_name,
                        user.last_name,
                        user.registration_date.isoformat() if user.registration_date else None,
                        1 if user.is_active else 0
                    )
                )
                self.conn.commit()
            
            self._disconnect()
            
            # Create chat
            self._connect()
            self.cursor.execute(
                "SELECT * FROM chats WHERE chat_id = ?",
                (chat.chat_id,)
            )
            existing_chat = self.cursor.fetchone()
            
            if not existing_chat:
                # Create chat
                logger.info(f"Creating new chat {chat.chat_id}")
                self.cursor.execute(
                    """
                    INSERT INTO chats (chat_id, title, chat_type, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        chat.chat_id,
                        chat.title,
                        chat.chat_type,
                        1 if chat.is_active else 0,
                        chat.created_at.isoformat() if chat.created_at else None
                    )
                )
                self.conn.commit()
            
            self._disconnect()
            
            # Create user-chat association
            self._connect()
            self.cursor.execute(
                "SELECT * FROM user_chats WHERE user_id = ? AND chat_id = ?",
                (user.user_id, chat.chat_id)
            )
            existing_user_chat = self.cursor.fetchone()
            
            if not existing_user_chat:
                # Create user-chat association
                logger.info(f"Creating new user-chat association for user {user.user_id} and chat {chat.chat_id}")
                now = datetime.datetime.now().isoformat()
                self.cursor.execute(
                    """
                    INSERT INTO user_chats (user_id, chat_id, joined_at, is_active)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user.user_id, chat.chat_id, now, 1)
                )
                self.conn.commit()
            elif not existing_user_chat['is_active']:
                # Reactivate user-chat association if it exists but is inactive
                logger.info(f"Reactivating user-chat association for user {user.user_id} and chat {chat.chat_id}")
                self.cursor.execute(
                    """
                    UPDATE user_chats
                    SET is_active = 1
                    WHERE user_id = ? AND chat_id = ?
                    """,
                    (user.user_id, chat.chat_id)
                )
                self.conn.commit()
            
            logger.info(f"Successfully registered user {user.user_id} in chat {chat.chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error registering user {user.user_id} in chat {chat.chat_id}: {e}")
            return False
        finally:
            self._disconnect()