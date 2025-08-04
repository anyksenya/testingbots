import logging
import datetime
from typing import Optional, List, Dict, Any

from database import DatabaseManager, Task
import config

logger = logging.getLogger(__name__)

class TaskService:
    """Service for task-related operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the task service.
        
        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
    
    def create_task(self, user_id: int, chat_id: int, description: str) -> Optional[int]:
        """Create a new task for a user in a chat.
        
        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            description: Task description.
            
        Returns:
            Task ID if creation was successful, None otherwise.
        """
        try:
            # Check if user is registered in the chat
            user_chat = self.db_manager.get_user_chat(user_id, chat_id)
            if not user_chat or not user_chat.is_active:
                logger.error(f"User {user_id} is not registered in chat {chat_id}")
                return None
            
            # Check if user has reached the maximum number of tasks for the week
            now = datetime.datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year
            
            task_count = self.db_manager.count_user_tasks_in_chat(user_id, chat_id, week_number, year)
            if task_count >= config.MAX_TASKS_PER_WEEK:
                logger.error(f"User {user_id} has reached the maximum number of tasks for the week")
                return None
            
            # Create task
            task = Task(
                user_id=user_id,
                chat_id=chat_id,
                description=description,
                status=config.TASK_STATUS['CREATED'],
                created_at=now,
                updated_at=now,
                week_number=week_number,
                year=year
            )
            
            task_id = self.db_manager.create_task(task)
            
            if task_id:
                logger.info(f"Task {task_id} created for user {user_id} in chat {chat_id}")
            else:
                logger.error(f"Failed to create task for user {user_id} in chat {chat_id}")
            
            return task_id
        except Exception as e:
            logger.error(f"Error creating task for user {user_id} in chat {chat_id}: {e}")
            return None
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: Task ID.
            
        Returns:
            Task object if found, None otherwise.
        """
        return self.db_manager.get_task(task_id)
    
    def get_user_tasks(self, user_id: int, chat_id: int, week_number: Optional[int] = None, 
                      year: Optional[int] = None) -> List[Task]:
        """Get tasks for a user in a chat, optionally filtered by week.
        
        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            week_number: Optional week number to filter by.
            year: Optional year to filter by.
            
        Returns:
            List of Task objects.
        """
        # If week_number and year are not provided, use current week
        if week_number is None or year is None:
            now = datetime.datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year
        
        return self.db_manager.get_user_tasks_in_chat(user_id, chat_id, week_number, year)
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """Update a task's status.
        
        Args:
            task_id: Task ID.
            status: New status (created, completed, canceled).
            
        Returns:
            True if the update was successful, False otherwise.
        """
        try:
            # Validate status
            if status not in config.TASK_STATUS.values():
                logger.error(f"Invalid task status: {status}")
                return False
            
            # Get task
            task = self.db_manager.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            # Update task status
            task.status = status
            task.updated_at = datetime.datetime.now()
            
            success = self.db_manager.update_task(task)
            
            if success:
                logger.info(f"Task {task_id} status updated to {status}")
            else:
                logger.error(f"Failed to update task {task_id} status")
            
            return success
        except Exception as e:
            logger.error(f"Error updating task {task_id} status: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task.
        
        Args:
            task_id: Task ID.
            
        Returns:
            True if the deletion was successful, False otherwise.
        """
        try:
            # Get task
            task = self.db_manager.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            # Delete task
            success = self.db_manager.delete_task(task_id)
            
            if success:
                logger.info(f"Task {task_id} deleted")
            else:
                logger.error(f"Failed to delete task {task_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    def can_create_task(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Check if a user can create a task in a chat.
        
        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            
        Returns:
            Dictionary with 'can_create' boolean and 'reason' string if can_create is False.
        """
        try:
            # Check if user is registered in the chat
            user_chat = self.db_manager.get_user_chat(user_id, chat_id)
            if not user_chat or not user_chat.is_active:
                return {
                    'can_create': False,
                    'reason': 'User is not registered in this chat'
                }
            
            # Check if user has reached the maximum number of tasks for the week
            now = datetime.datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year
            
            task_count = self.db_manager.count_user_tasks_in_chat(user_id, chat_id, week_number, year)
            if task_count >= config.MAX_TASKS_PER_WEEK:
                return {
                    'can_create': False,
                    'reason': f'Maximum number of tasks ({config.MAX_TASKS_PER_WEEK}) reached for this week'
                }
            
            # Check if user has reached the minimum number of tasks for the week
            # task_count is the current count before adding the new task
            # We need to calculate how many more tasks are needed after this one
            if (task_count + 1) < config.MIN_TASKS_PER_WEEK:  # +1 for the task we're about to create
                remaining = config.MIN_TASKS_PER_WEEK - (task_count + 1)
                return {
                    'can_create': True,
                    'min_tasks_remaining': remaining
                }
            
            return {'can_create': True}
        except Exception as e:
            logger.error(f"Error checking if user {user_id} can create task in chat {chat_id}: {e}")
            return {
                'can_create': False,
                'reason': 'An error occurred'
            }
    
    def get_task_stats(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Get task statistics for a user in a chat.
        
        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            
        Returns:
            Dictionary with task statistics.
        """
        try:
            # Get current week and year
            now = datetime.datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year
            
            # Get tasks for current week
            tasks = self.db_manager.get_user_tasks_in_chat(user_id, chat_id, week_number, year)
            
            # Count tasks by status
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.status == config.TASK_STATUS['COMPLETED'])
            canceled_tasks = sum(1 for task in tasks if task.status == config.TASK_STATUS['CANCELED'])
            created_tasks = sum(1 for task in tasks if task.status == config.TASK_STATUS['CREATED'])
            
            # Calculate completion rate
            completion_rate = 0.0
            if total_tasks > 0:
                completion_rate = completed_tasks / total_tasks
            
            return {
                'user_id': user_id,
                'chat_id': chat_id,
                'week_number': week_number,
                'year': year,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'canceled_tasks': canceled_tasks,
                'created_tasks': created_tasks,
                'completion_rate': completion_rate,
                'min_tasks': config.MIN_TASKS_PER_WEEK,
                'max_tasks': config.MAX_TASKS_PER_WEEK
            }
        except Exception as e:
            logger.error(f"Error getting task stats for user {user_id} in chat {chat_id}: {e}")
            return {}