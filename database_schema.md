# Telegram Task Bot Database Schema

This document describes the database schema used by the Telegram Task Bot. The bot uses SQLite as its database engine.

## Overview

The database consists of five main tables:

1. `users` - Stores information about registered users
2. `chats` - Stores information about chats where the bot is used
3. `user_chats` - Stores the many-to-many relationship between users and chats
4. `tasks` - Stores tasks created by users
5. `weekly_stats` - Stores weekly statistics for users

## Tables

### users

Stores information about registered Telegram users.

| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Primary key, Telegram user ID |
| username | TEXT | Telegram username (optional) |
| first_name | TEXT | User's first name |
| last_name | TEXT | User's last name (optional) |
| registration_date | TEXT | ISO format date when the user registered |
| is_active | INTEGER | Boolean (0/1) indicating if the user is active |

### chats

Stores information about Telegram chats where the bot is used.

| Column | Type | Description |
|--------|------|-------------|
| chat_id | INTEGER | Primary key, Telegram chat ID |
| title | TEXT | Chat title (for group chats) |
| chat_type | TEXT | Type of chat (private, group, supergroup, channel) |
| is_active | INTEGER | Boolean (0/1) indicating if the chat is active |
| created_at | TEXT | ISO format date when the chat was added |

### user_chats

Stores the many-to-many relationship between users and chats.

| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Foreign key to users.user_id |
| chat_id | INTEGER | Foreign key to chats.chat_id |
| joined_at | TEXT | ISO format date when the user joined the chat |
| is_active | INTEGER | Boolean (0/1) indicating if the user is active in the chat |

Primary key is the combination of (user_id, chat_id).

### tasks

Stores tasks created by users.

| Column | Type | Description |
|--------|------|-------------|
| task_id | INTEGER | Primary key, auto-incrementing |
| user_id | INTEGER | Foreign key to users.user_id |
| chat_id | INTEGER | Foreign key to chats.chat_id |
| description | TEXT | Task description |
| status | TEXT | Task status (created, completed, canceled) |
| created_at | TEXT | ISO format date when the task was created |
| updated_at | TEXT | ISO format date when the task was last updated |
| week_number | INTEGER | ISO week number when the task was created |
| year | INTEGER | Year when the task was created |

### weekly_stats

Stores weekly statistics for users.

| Column | Type | Description |
|--------|------|-------------|
| stat_id | INTEGER | Primary key, auto-incrementing |
| user_id | INTEGER | Foreign key to users.user_id |
| chat_id | INTEGER | Foreign key to chats.chat_id |
| week_number | INTEGER | ISO week number for the statistics |
| year | INTEGER | Year for the statistics |
| tasks_created | INTEGER | Number of tasks created in the week |
| tasks_completed | INTEGER | Number of tasks completed in the week |
| tasks_canceled | INTEGER | Number of tasks canceled in the week |
| completion_rate | REAL | Ratio of completed tasks to total tasks |

## Relationships

The following relationships exist between the tables:

1. A user can be in multiple chats (one-to-many relationship from users to user_chats)
2. A chat can have multiple users (one-to-many relationship from chats to user_chats)
3. A user can have multiple tasks in a chat (one-to-many relationship from users and chats to tasks)
4. A user can have multiple weekly statistics in a chat (one-to-many relationship from users and chats to weekly_stats)

## Indexes

The following indexes are recommended for optimal performance:

1. Index on (user_id, chat_id, week_number, year) in the tasks table
2. Index on (user_id, chat_id, week_number, year) in the weekly_stats table

## Constraints

The following constraints are enforced:

1. Foreign key constraints from user_chats to users and chats
2. Foreign key constraints from tasks to users and chats
3. Foreign key constraints from weekly_stats to users and chats

## Database Initialization

The database is initialized when the bot starts for the first time. The initialization code creates all the necessary tables if they don't exist.

## Database Migrations

The bot does not currently have a formal migration system. If the schema needs to be updated, manual migrations should be performed.

## Example Queries

### Get all tasks for a user in a chat for the current week

```sql
SELECT * FROM tasks
WHERE user_id = ? AND chat_id = ? AND week_number = ? AND year = ?
```

### Get weekly statistics for a user in a chat

```sql
SELECT * FROM weekly_stats
WHERE user_id = ? AND chat_id = ? AND week_number = ? AND year = ?
```

### Get all users in a chat

```sql
SELECT u.* FROM users u
JOIN user_chats uc ON u.user_id = uc.user_id
WHERE uc.chat_id = ? AND uc.is_active = 1 AND u.is_active = 1
```

### Get completion rates for all users in a chat

```sql
SELECT u.user_id, u.username, u.first_name, u.last_name, ws.completion_rate
FROM users u
JOIN user_chats uc ON u.user_id = uc.user_id
LEFT JOIN weekly_stats ws ON u.user_id = ws.user_id AND uc.chat_id = ws.chat_id AND ws.week_number = ? AND ws.year = ?
WHERE uc.chat_id = ? AND uc.is_active = 1 AND u.is_active = 1
```

## Maintenance

### Backing Up the Database

To back up the database, simply copy the database file:

```bash
cp taskbot.db taskbot_backup.db
```

### Restoring from Backup

To restore from a backup, replace the database file:

```bash
cp taskbot_backup.db taskbot.db
```

### Optimizing the Database

To optimize the database, run the VACUUM command:

```sql
VACUUM;
```

### Checking Database Integrity

To check the integrity of the database, run the integrity_check pragma:

```sql
PRAGMA integrity_check;