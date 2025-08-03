import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Bot configuration
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
if not TELEGRAM_API_TOKEN:
    raise ValueError("No TELEGRAM_API_TOKEN found in .env file")

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'sqlite:///taskbot.db')

# Timezone configuration
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')

# Application paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / 'database'

# Ensure database directory exists
DATABASE_DIR.mkdir(exist_ok=True)

# Task status constants
TASK_STATUS = {
    'CREATED': 'created',
    'COMPLETED': 'completed',
    'CANCELED': 'canceled'
}

# Task limits
MIN_TASKS_PER_WEEK = 3
MAX_TASKS_PER_WEEK = 5

# Schedule times (UTC+3)
WEEKLY_STATS_DAY = 'friday'
WEEKLY_STATS_HOUR = 17
WEEKLY_STATS_MINUTE = 0

WEEKLY_RESET_DAY = 'monday'
WEEKLY_RESET_HOUR = 0
WEEKLY_RESET_MINUTE = 0