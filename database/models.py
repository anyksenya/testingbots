import sqlite3
import datetime
from typing import Dict, List, Optional, Tuple, Any

class User:
    """User model representing a registered Telegram user."""
    
    def __init__(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        registration_date: Optional[datetime.datetime] = None,
        is_active: bool = True
    ):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.registration_date = registration_date or datetime.datetime.now()
        self.is_active = is_active
    
    @classmethod
    def from_row(cls, row: Tuple) -> 'User':
        """Create a User instance from a database row."""
        return cls(
            user_id=row[0],
            username=row[1],
            first_name=row[2],
            last_name=row[3],
            registration_date=datetime.datetime.fromisoformat(row[4]) if row[4] else None,
            is_active=bool(row[5])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert User instance to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'is_active': self.is_active
        }


class Chat:
    """Chat model representing a Telegram chat."""
    
    def __init__(
        self,
        chat_id: int,
        title: Optional[str] = None,
        chat_type: str = "private",
        is_active: bool = True,
        created_at: Optional[datetime.datetime] = None
    ):
        self.chat_id = chat_id
        self.title = title
        self.chat_type = chat_type  # private, group, supergroup, channel
        self.is_active = is_active
        self.created_at = created_at or datetime.datetime.now()
    
    @classmethod
    def from_row(cls, row: Tuple) -> 'Chat':
        """Create a Chat instance from a database row."""
        return cls(
            chat_id=row[0],
            title=row[1],
            chat_type=row[2],
            is_active=bool(row[3]),
            created_at=datetime.datetime.fromisoformat(row[4]) if row[4] else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Chat instance to dictionary."""
        return {
            'chat_id': self.chat_id,
            'title': self.title,
            'chat_type': self.chat_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserChat:
    """Association between a User and a Chat."""
    
    def __init__(
        self,
        user_id: int,
        chat_id: int,
        joined_at: Optional[datetime.datetime] = None,
        is_active: bool = True
    ):
        self.user_id = user_id
        self.chat_id = chat_id
        self.joined_at = joined_at or datetime.datetime.now()
        self.is_active = is_active
    
    @classmethod
    def from_row(cls, row: Tuple) -> 'UserChat':
        """Create a UserChat instance from a database row."""
        return cls(
            user_id=row[0],
            chat_id=row[1],
            joined_at=datetime.datetime.fromisoformat(row[2]) if row[2] else None,
            is_active=bool(row[3])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert UserChat instance to dictionary."""
        return {
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'is_active': self.is_active
        }


class Task:
    """Task model representing a user's task in a specific chat."""
    
    def __init__(
        self,
        task_id: Optional[int] = None,
        user_id: int = 0,
        chat_id: int = 0,
        description: str = "",
        status: str = "created",
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
        week_number: Optional[int] = None,
        year: Optional[int] = None
    ):
        self.task_id = task_id
        self.user_id = user_id
        self.chat_id = chat_id
        self.description = description
        self.status = status
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or datetime.datetime.now()
        
        # If week_number and year are not provided, calculate from created_at
        if week_number is None or year is None:
            current_date = self.created_at
            self.week_number = current_date.isocalendar()[1]  # ISO week number
            self.year = current_date.year
        else:
            self.week_number = week_number
            self.year = year
    
    @classmethod
    def from_row(cls, row: Tuple) -> 'Task':
        """Create a Task instance from a database row."""
        return cls(
            task_id=row[0],
            user_id=row[1],
            chat_id=row[2],
            description=row[3],
            status=row[4],
            created_at=datetime.datetime.fromisoformat(row[5]) if row[5] else None,
            updated_at=datetime.datetime.fromisoformat(row[6]) if row[6] else None,
            week_number=row[7],
            year=row[8]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Task instance to dictionary."""
        return {
            'task_id': self.task_id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'week_number': self.week_number,
            'year': self.year
        }


class WeeklyStat:
    """Weekly statistics model for a user in a specific chat."""
    
    def __init__(
        self,
        stat_id: Optional[int] = None,
        user_id: int = 0,
        chat_id: int = 0,
        week_number: int = 0,
        year: int = 0,
        tasks_created: int = 0,
        tasks_completed: int = 0,
        tasks_canceled: int = 0,
        completion_rate: float = 0.0
    ):
        self.stat_id = stat_id
        self.user_id = user_id
        self.chat_id = chat_id
        self.week_number = week_number
        self.year = year
        self.tasks_created = tasks_created
        self.tasks_completed = tasks_completed
        self.tasks_canceled = tasks_canceled
        self.completion_rate = completion_rate
    
    @classmethod
    def from_row(cls, row: Tuple) -> 'WeeklyStat':
        """Create a WeeklyStat instance from a database row."""
        return cls(
            stat_id=row[0],
            user_id=row[1],
            chat_id=row[2],
            week_number=row[3],
            year=row[4],
            tasks_created=row[5],
            tasks_completed=row[6],
            tasks_canceled=row[7],
            completion_rate=row[8]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert WeeklyStat instance to dictionary."""
        return {
            'stat_id': self.stat_id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'week_number': self.week_number,
            'year': self.year,
            'tasks_created': self.tasks_created,
            'tasks_completed': self.tasks_completed,
            'tasks_canceled': self.tasks_canceled,
            'completion_rate': self.completion_rate
        }