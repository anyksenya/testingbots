"""
Statistics service for the Telegram Task Bot.
This module handles generation and storage of weekly statistics.
"""

import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple

from database import DatabaseManager, WeeklyStat, User
import config

logger = logging.getLogger(__name__)

class StatisticsService:
    """Service for statistics-related operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the statistics service.
        
        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
    
    def generate_weekly_stats_for_chat(self, chat_id: int) -> List[WeeklyStat]:
        """Generate weekly statistics for all users in a specific chat.
        
        Args:
            chat_id: Telegram chat ID.
            
        Returns:
            List of WeeklyStat objects.
        """
        try:
            # Get current week and year
            now = datetime.datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year
            
            # Get all users in the chat
            users = self.db_manager.get_chat_users(chat_id)
            logger.info(f"Found {len(users)} users in chat {chat_id}")
            
            stats = []
            for user in users:
                try:
                    # Get user's tasks for the current week
                    tasks = self.db_manager.get_user_tasks_in_chat(user.user_id, chat_id, week_number, year)
                    logger.info(f"Found {len(tasks)} tasks for user {user.user_id} in chat {chat_id}")
                    
                    # Count tasks by status
                    total_tasks = len(tasks)
                    completed_tasks = sum(1 for task in tasks if task.status == 'completed')
                    canceled_tasks = sum(1 for task in tasks if task.status == 'canceled')
                    
                    # Calculate completion rate
                    completion_rate = 0.0
                    if total_tasks > 0:
                        completion_rate = completed_tasks / total_tasks
                    
                    # Create or update weekly stat
                    stat = WeeklyStat(
                        user_id=user.user_id,
                        chat_id=chat_id,
                        week_number=week_number,
                        year=year,
                        tasks_created=total_tasks,
                        tasks_completed=completed_tasks,
                        tasks_canceled=canceled_tasks,
                        completion_rate=completion_rate
                    )
                    
                    # Try to save to database, but don't fail if it doesn't work
                    try:
                        success = self.db_manager.create_or_update_weekly_stat(stat)
                        if success:
                            logger.info(f"Updated statistics for user {user.user_id} in chat {chat_id}")
                        else:
                            logger.error(f"Failed to update statistics for user {user.user_id} in chat {chat_id}")
                    except Exception as e:
                        logger.error(f"Error saving statistics for user {user.user_id} in chat {chat_id}: {e}")
                    
                    # Add to stats list regardless of whether it was saved to the database
                    stats.append(stat)
                except Exception as e:
                    logger.error(f"Error processing user {user.user_id} in chat {chat_id}: {e}")
                    continue
            
            logger.info(f"Generated weekly statistics for chat {chat_id}")
            return stats
        except Exception as e:
            logger.error(f"Error generating weekly statistics for chat {chat_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def generate_weekly_stats_for_all_chats(self) -> Dict[int, List[WeeklyStat]]:
        """Generate weekly statistics for all users in all active chats.
        
        Returns:
            Dictionary mapping chat IDs to lists of WeeklyStat objects.
        """
        try:
            # Get all active chats
            chats = self.db_manager.get_all_active_chats()
            
            results = {}
            for chat in chats:
                stats = self.generate_weekly_stats_for_chat(chat.chat_id)
                results[chat.chat_id] = stats
            
            logger.info("Generated weekly statistics for all chats")
            return results
        except Exception as e:
            logger.error(f"Error generating weekly statistics for all chats: {e}")
            return {}
    
    def get_weekly_stats(self, user_id: int, chat_id: int, week_number: Optional[int] = None, 
                        year: Optional[int] = None) -> Optional[WeeklyStat]:
        """Get weekly statistics for a user in a specific chat.
        
        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            week_number: Optional week number to filter by.
            year: Optional year to filter by.
            
        Returns:
            WeeklyStat object if found, None otherwise.
        """
        try:
            # If week_number and year are not provided, use current week
            if week_number is None or year is None:
                now = datetime.datetime.now()
                week_number = now.isocalendar()[1]
                year = now.year
            
            # Get statistics
            stat = self.db_manager.get_weekly_stat(user_id, chat_id, week_number, year)
            
            return stat
        except Exception as e:
            logger.error(f"Error getting weekly statistics for user {user_id} in chat {chat_id}: {e}")
            return None
    
    def get_stats_history(self, user_id: int, chat_id: int, limit: int = 10) -> List[WeeklyStat]:
        """Get historical weekly statistics for a user in a specific chat.
        
        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            limit: Maximum number of statistics to return.
            
        Returns:
            List of WeeklyStat objects.
        """
        try:
            # Get statistics history
            stats = self.db_manager.get_user_stats_history_in_chat(user_id, chat_id, limit)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics history for user {user_id} in chat {chat_id}: {e}")
            return []
    
    def get_chat_users_completion_rates(self, chat_id: int, week_number: Optional[int] = None, 
                                       year: Optional[int] = None) -> List[Tuple[int, str, float]]:
        """Get completion rates for all users in a chat.
        
        Args:
            chat_id: Telegram chat ID.
            week_number: Optional week number to filter by.
            year: Optional year to filter by.
            
        Returns:
            List of tuples containing (user_id, username, completion_rate).
        """
        try:
            # If week_number and year are not provided, use current week
            if week_number is None or year is None:
                now = datetime.datetime.now()
                week_number = now.isocalendar()[1]
                year = now.year
            
            # Get all users in the chat
            users = self.db_manager.get_chat_users(chat_id)
            
            # Get completion rates for each user
            result = []
            for user in users:
                try:
                    # Try to get user's weekly stats from database
                    stat = self.db_manager.get_weekly_stat(user.user_id, chat_id, week_number, year)
                    
                    # If no stats found, calculate them from tasks
                    if not stat:
                        tasks = self.db_manager.get_user_tasks_in_chat(user.user_id, chat_id, week_number, year)
                        
                        # Count tasks by status
                        total_tasks = len(tasks)
                        completed_tasks = sum(1 for task in tasks if task.status == 'completed')
                        
                        # Calculate completion rate
                        completion_rate = 0.0
                        if total_tasks > 0:
                            completion_rate = completed_tasks / total_tasks
                    else:
                        # Use stats from database
                        completion_rate = 0.0
                        if stat.tasks_created > 0:
                            completion_rate = stat.tasks_completed / stat.tasks_created
                    
                    # Add to result
                    username = user.username or f"{user.first_name} {user.last_name or ''}"
                    result.append((user.user_id, username.strip(), completion_rate))
                except Exception as e:
                    logger.error(f"Error getting completion rate for user {user.user_id}: {e}")
                    # Add user with 0% completion rate
                    username = user.username or f"{user.first_name} {user.last_name or ''}"
                    result.append((user.user_id, username.strip(), 0.0))
            
            return result
        except Exception as e:
            logger.error(f"Error getting completion rates for chat {chat_id}: {e}")
            return []
    
    def format_weekly_stats(self, stat: WeeklyStat) -> str:
        """Format weekly statistics for display.
        
        Args:
            stat: WeeklyStat object.
            
        Returns:
            Formatted statistics string.
        """
        if not stat:
            return "No statistics available."
        
        # Format statistics
        stats_text = f"📊 Weekly Statistics (Week {stat.week_number}, {stat.year}):\n\n"
        stats_text += f"Total tasks: {stat.tasks_created}\n"
        stats_text += f"Completed tasks: {stat.tasks_completed}\n"
        stats_text += f"Canceled tasks: {stat.tasks_canceled}\n"
        stats_text += f"Completion rate: {stat.completion_rate * 100:.1f}%\n"
        
        return stats_text
    
    def format_chat_completion_rates(self, chat_id: int, week_number: Optional[int] = None,
                                    year: Optional[int] = None) -> str:
        """Format completion rates for all users in a chat.
        
        Args:
            chat_id: Telegram chat ID.
            week_number: Optional week number to filter by.
            year: Optional year to filter by.
            
        Returns:
            Formatted completion rates string.
        """
        try:
            # If week_number and year are not provided, use current week
            if week_number is None or year is None:
                now = datetime.datetime.now()
                week_number = now.isocalendar()[1]
                year = now.year
            
            # Get completion rates
            completion_rates = self.get_chat_users_completion_rates(chat_id, week_number, year)
            
            if not completion_rates:
                # Try to generate statistics on the fly
                logger.info(f"No statistics found for chat {chat_id}, generating on the fly")
                self.generate_weekly_stats_for_chat(chat_id)
                
                # Try again to get completion rates
                completion_rates = self.get_chat_users_completion_rates(chat_id, week_number, year)
                
                if not completion_rates:
                    return "No statistics available for this chat."
            
            # Format completion rates
            stats_text = f"📊 Chat Completion Rates (Week {week_number}, {year}):\n\n"
            
            for user_id, username, completion_rate in completion_rates:
                stats_text += f"{username} ({user_id}): {completion_rate * 100:.1f}%\n"
            
            return stats_text
        except Exception as e:
            logger.error(f"Error formatting chat completion rates for chat {chat_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "Error generating statistics. Please try again later."
    
    def format_stats_history(self, stats: List[WeeklyStat]) -> str:
        """Format historical statistics for display.
        
        Args:
            stats: List of WeeklyStat objects.
            
        Returns:
            Formatted statistics string.
        """
        if not stats:
            return "No historical statistics available."
        
        # Format statistics
        history_text = "📈 Historical Weekly Statistics:\n\n"
        
        for stat in stats:
            history_text += f"Week {stat.week_number}, {stat.year}:\n"
            history_text += f"  Total tasks: {stat.tasks_created}\n"
            history_text += f"  Completed: {stat.tasks_completed}\n"
            history_text += f"  Canceled: {stat.tasks_canceled}\n"
            history_text += f"  Completion rate: {stat.completion_rate * 100:.1f}%\n\n"
        
        return history_text
    
    def reset_weekly_tasks(self) -> bool:
        """Reset weekly tasks for all users in all chats.
        
        This method is called by the scheduler at the beginning of each week.
        It generates statistics for the previous week and archives them.
        
        Returns:
            True if the reset was successful, False otherwise.
        """
        try:
            # First, generate statistics for all chats to ensure we have a record
            self.generate_weekly_stats_for_all_chats()
            
            # TODO: Implement task archiving if needed
            
            logger.info("Weekly tasks reset completed")
            return True
        except Exception as e:
            logger.error(f"Error resetting weekly tasks: {e}")
            return False