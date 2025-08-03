import logging
from typing import Optional, List, Dict, Any

from database import DatabaseManager, User, Chat, UserChat
from database.models import User, Chat, UserChat

logger = logging.getLogger(__name__)

class UserService:
    """Service for user-related operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the user service.
        
        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
    
    def register_user(self, user_id: int, username: Optional[str], first_name: Optional[str], 
                     last_name: Optional[str], chat_id: int, chat_title: Optional[str], 
                     chat_type: str) -> bool:
        """Register a user in a chat.
        
        Args:
            user_id: Telegram user ID.
            username: Telegram username.
            first_name: User's first name.
            last_name: User's last name.
            chat_id: Telegram chat ID.
            chat_title: Chat title.
            chat_type: Chat type (private, group, supergroup, channel).
            
        Returns:
            True if registration was successful, False otherwise.
        """
        try:
            # Create User and Chat objects
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            chat = Chat(
                chat_id=chat_id,
                title=chat_title if chat_title else f"{first_name}'s chat",
                chat_type=chat_type
            )
            
            # Register user in chat
            success = self.db_manager.register_user_in_chat(user, chat)
            
            if success:
                logger.info(f"User {user_id} registered in chat {chat_id}")
            else:
                logger.error(f"Failed to register user {user_id} in chat {chat_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error registering user {user_id} in chat {chat_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: Telegram user ID.
            
        Returns:
            User object if found, None otherwise.
        """
        return self.db_manager.get_user(user_id)
    
    def get_user_chats(self, user_id: int) -> List[Chat]:
        """Get all chats for a user.
        
        Args:
            user_id: Telegram user ID.
            
        Returns:
            List of Chat objects.
        """
        return self.db_manager.get_user_chats(user_id)
    
    def is_user_registered(self, user_id: int, chat_id: int) -> bool:
        """Check if a user is registered in a chat.
        
        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            
        Returns:
            True if the user is registered in the chat, False otherwise.
        """
        user_chat = self.db_manager.get_user_chat(user_id, chat_id)
        return user_chat is not None and user_chat.is_active
    
    def update_user_profile(self, user_id: int, username: Optional[str] = None, 
                           first_name: Optional[str] = None, last_name: Optional[str] = None) -> bool:
        """Update a user's profile.
        
        Args:
            user_id: Telegram user ID.
            username: New username.
            first_name: New first name.
            last_name: New last name.
            
        Returns:
            True if the update was successful, False otherwise.
        """
        try:
            # Get existing user
            user = self.db_manager.get_user(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            # Update user fields if provided
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            
            # Save updated user
            success = self.db_manager.update_user(user)
            
            if success:
                logger.info(f"User {user_id} profile updated")
            else:
                logger.error(f"Failed to update user {user_id} profile")
            
            return success
        except Exception as e:
            logger.error(f"Error updating user {user_id} profile: {e}")
            return False
    
    def get_user_stats(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Get statistics for a user in a chat.
        
        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            
        Returns:
            Dictionary with user statistics.
        """
        try:
            # Get user and chat
            user = self.db_manager.get_user(user_id)
            chat = self.db_manager.get_chat(chat_id)
            
            if not user or not chat:
                logger.error(f"User {user_id} or chat {chat_id} not found")
                return {}
            
            # Get current week stats
            import datetime
            now = datetime.datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year
            
            weekly_stat = self.db_manager.get_weekly_stat(user_id, chat_id, week_number, year)
            
            if not weekly_stat:
                # No stats for current week, return empty stats
                return {
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'week_number': week_number,
                    'year': year,
                    'tasks_created': 0,
                    'tasks_completed': 0,
                    'tasks_canceled': 0,
                    'completion_rate': 0.0
                }
            
            return weekly_stat.to_dict()
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id} in chat {chat_id}: {e}")
            return {}