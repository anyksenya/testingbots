#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Task Management Bot
A bot that helps users manage their weekly tasks.
"""

import logging
import sys
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

import config
from database import DatabaseManager
from services import UserService

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize services
db_manager = DatabaseManager()
user_service = UserService(db_manager)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Register user in the database using UserService
    success = user_service.register_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        chat_id=chat.id,
        chat_title=chat.title,
        chat_type=chat.type
    )
    
    await update.message.reply_text(
        f'Hi {user.first_name}! I am your Task Management Bot.\n\n'
        f'I can help you manage your weekly tasks.\n'
        f'Use /help to see available commands.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot and register as a user\n"
        "/help - Show this help message\n"
        "/add_task - Add a new task for the current week\n"
        "/my_tasks - Show your tasks for the current week\n"
        "/update_task - Update the status of a task\n"
        "/stats - Show your statistics for the current week\n"
        "/history - Show your historical weekly statistics"
    )
    await update.message.reply_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(f"Error: {context.error} caused by {update}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(config.TELEGRAM_API_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()
    logger.info("Bot started")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)