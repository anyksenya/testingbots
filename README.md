# Telegram Task Management Bot

A Telegram bot that helps users manage their weekly tasks. The bot allows users to register, create 3-5 tasks per week, track task statuses, and receive weekly statistics.

## Features

- User registration
- Weekly task management (3-5 tasks per week)
- Task status tracking (created, completed, canceled)
- Weekly statistics generation (every Friday at 17:00 UTC+3)
- Weekly task reset (every Monday at 00:00 UTC+3)

## Requirements

- Python 3.8+
- python-telegram-bot
- APScheduler
- python-dotenv

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram-task-bot.git
cd telegram-task-bot
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

5. Edit the `.env` file and add your Telegram Bot API token (get it from [@BotFather](https://t.me/BotFather)):
```
TELEGRAM_API_TOKEN=your_telegram_bot_token_here
```

6. Run the bot:
```bash
python bot.py
```

## Usage

- `/start` - Start the bot and register as a user
- `/help` - Show available commands
- `/add_task` - Add a new task for the current week
- `/my_tasks` - Show your tasks for the current week
- `/update_task` - Update the status of a task
- `/stats` - Show your statistics for the current week
- `/history` - Show your historical weekly statistics

## Project Structure

```
telegram-task-bot/
├── bot.py                 # Main bot application
├── config.py              # Configuration settings
├── database/
│   ├── __init__.py
│   ├── manager.py         # Database connection and operations
│   └── models.py          # Database models
├── handlers/
│   ├── __init__.py
│   ├── command_handler.py # Command processing
│   ├── message_handler.py # Message processing
│   └── callback_handler.py # Callback query processing
├── services/
│   ├── __init__.py
│   ├── task_service.py    # Task management logic
│   ├── user_service.py    # User management logic
│   └── stats_service.py   # Statistics generation
├── utils/
│   ├── __init__.py
│   ├── scheduler.py       # Scheduling functionality
│   └── helpers.py         # Helper functions
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## License

MIT