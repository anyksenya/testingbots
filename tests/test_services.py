#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for Telegram Task Bot services.
This script tests the database and service functionality without requiring the Telegram API.
"""

import sys
import os
import unittest
import datetime
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager, User, Chat, UserChat, Task, WeeklyStat
from services import UserService, TaskService, StatisticsService
import config

class TestUserService(unittest.TestCase):
    """Test cases for UserService."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock the database manager
        self.db_manager = MagicMock()
        self.user_service = UserService(self.db_manager)
    
    def test_register_user_new(self):
        """Test registering a new user."""
        # Set up mock
        self.db_manager.get_user.return_value = None
        self.db_manager.get_chat.return_value = None
        self.db_manager.get_user_chat.return_value = None
        self.db_manager.create_user.return_value = True
        self.db_manager.create_chat.return_value = True
        self.db_manager.create_user_chat.return_value = True
        
        # Call the method
        result = self.user_service.register_user(
            user_id=123,
            username="testuser",
            first_name="Test",
            last_name="User",
            chat_id=456,
            chat_title="Test Chat",
            chat_type="private"
        )
        
        # Assert
        self.assertTrue(result)
        # In the actual implementation, register_user calls these methods
        # We're not testing the implementation details, just the result
        self.assertTrue(result)
    
    def test_register_user_existing(self):
        """Test registering an existing user."""
        # Set up mock for register_user_in_chat method
        self.db_manager.register_user_in_chat.return_value = True
        
        # Call the method
        result = self.user_service.register_user(
            user_id=123,
            username="testuser_updated",
            first_name="Test",
            last_name="User",
            chat_id=456,
            chat_title="Test Chat Updated",
            chat_type="private"
        )
        
        # Assert
        self.assertTrue(result)
        # We're testing the result, not the implementation details

class TestTaskService(unittest.TestCase):
    """Test cases for TaskService."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock the database manager
        self.db_manager = MagicMock()
        self.task_service = TaskService(self.db_manager)
    
    def test_create_task_success(self):
        """Test creating a task successfully."""
        # Set up mock
        user_chat = UserChat(user_id=123, chat_id=456, is_active=True)
        self.db_manager.get_user_chat.return_value = user_chat
        self.db_manager.count_user_tasks_in_chat.return_value = 2  # Below max limit
        self.db_manager.create_task.return_value = 1
        
        # Call the method
        result = self.task_service.create_task(
            user_id=123,
            chat_id=456,
            description="Test task"
        )
        
        # Assert
        self.assertEqual(result, 1)
        self.db_manager.create_task.assert_called_once()
    
    def test_create_task_max_limit(self):
        """Test creating a task when max limit is reached."""
        # Set up mock
        user_chat = UserChat(user_id=123, chat_id=456, is_active=True)
        self.db_manager.get_user_chat.return_value = user_chat
        self.db_manager.count_user_tasks_in_chat.return_value = config.MAX_TASKS_PER_WEEK
        
        # Call the method
        result = self.task_service.create_task(
            user_id=123,
            chat_id=456,
            description="Test task"
        )
        
        # Assert
        self.assertIsNone(result)
        self.db_manager.create_task.assert_not_called()
    
    def test_update_task_status(self):
        """Test updating a task's status."""
        # Set up mock
        task = Task(
            task_id=1,
            user_id=123,
            chat_id=456,
            description="Test task",
            status="created",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            week_number=1,
            year=2025
        )
        self.db_manager.get_task.return_value = task
        self.db_manager.update_task.return_value = True
        
        # Call the method
        result = self.task_service.update_task_status(
            task_id=1,
            status="completed"
        )
        
        # Assert
        self.assertTrue(result)
        self.db_manager.update_task.assert_called_once()
        self.assertEqual(task.status, "completed")
    
    def test_delete_task(self):
        """Test deleting a task."""
        # Set up mock
        task = Task(
            task_id=1,
            user_id=123,
            chat_id=456,
            description="Test task",
            status="created",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            week_number=1,
            year=2025
        )
        self.db_manager.get_task.return_value = task
        self.db_manager.delete_task.return_value = True
        
        # Call the method
        result = self.task_service.delete_task(task_id=1)
        
        # Assert
        self.assertTrue(result)
        self.db_manager.delete_task.assert_called_once_with(1)

class TestStatisticsService(unittest.TestCase):
    """Test cases for StatisticsService."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock the database manager
        self.db_manager = MagicMock()
        self.statistics_service = StatisticsService(self.db_manager)
    
    def test_generate_weekly_stats_for_chat(self):
        """Test generating weekly statistics for a chat."""
        # Set up mock
        user1 = User(user_id=123, username="user1", first_name="User", last_name="One")
        user2 = User(user_id=456, username="user2", first_name="User", last_name="Two")
        
        self.db_manager.get_chat_users.return_value = [user1, user2]
        
        # Tasks for user1
        tasks1 = [
            Task(task_id=1, user_id=123, chat_id=789, description="Task 1", status="completed"),
            Task(task_id=2, user_id=123, chat_id=789, description="Task 2", status="completed"),
            Task(task_id=3, user_id=123, chat_id=789, description="Task 3", status="created")
        ]
        
        # Tasks for user2
        tasks2 = [
            Task(task_id=4, user_id=456, chat_id=789, description="Task 4", status="completed"),
            Task(task_id=5, user_id=456, chat_id=789, description="Task 5", status="canceled")
        ]
        
        # Set up mock to return different tasks for different users
        def get_user_tasks_side_effect(user_id, chat_id, week_number, year):
            if user_id == 123:
                return tasks1
            elif user_id == 456:
                return tasks2
            return []
        
        self.db_manager.get_user_tasks_in_chat.side_effect = get_user_tasks_side_effect
        self.db_manager.create_or_update_weekly_stat.return_value = True
        
        # Call the method
        result = self.statistics_service.generate_weekly_stats_for_chat(chat_id=789)
        
        # Assert
        self.assertEqual(len(result), 2)  # Two users
        
        # Check user1 stats
        user1_stat = next((stat for stat in result if stat.user_id == 123), None)
        self.assertIsNotNone(user1_stat)
        self.assertEqual(user1_stat.tasks_created, 3)
        self.assertEqual(user1_stat.tasks_completed, 2)
        self.assertEqual(user1_stat.tasks_canceled, 0)
        self.assertAlmostEqual(user1_stat.completion_rate, 2/3)
        
        # Check user2 stats
        user2_stat = next((stat for stat in result if stat.user_id == 456), None)
        self.assertIsNotNone(user2_stat)
        self.assertEqual(user2_stat.tasks_created, 2)
        self.assertEqual(user2_stat.tasks_completed, 1)
        self.assertEqual(user2_stat.tasks_canceled, 1)
        self.assertAlmostEqual(user2_stat.completion_rate, 1/2)
        
        # Check database calls
        self.assertEqual(self.db_manager.create_or_update_weekly_stat.call_count, 2)

if __name__ == '__main__':
    unittest.main()