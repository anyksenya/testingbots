#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Test Bot
A minimal bot to test the python-telegram-bot library.
"""

import logging
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define a few command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! I am a simple test bot.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help!')

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token("7522167173:AAFpBoJsOmA0oY3EIKsIh2X24GWqqS03zTk").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    application.run_polling()
    logger.info("Bot started")

if __name__ == '__main__':
    main()