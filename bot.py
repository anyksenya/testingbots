#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Task Management Bot
A bot that helps users manage their weekly tasks.
"""

import logging
import sys
import json
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

import config
from database import DatabaseManager
from services import UserService, TaskService
from handlers import ConversationHandlers

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize services
db_manager = DatabaseManager()
user_service = UserService(db_manager)
task_service = TaskService(db_manager)

# Initialize conversation handlers
conversation_handlers = ConversationHandlers(task_service, user_service)

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
        "/add_task_conv - Add a new task using conversation flow\n"
        "/my_tasks - Show your tasks for the current week\n"
        "/update_task - Update the status of a task\n"
        "/update_task_conv - Update task status using conversation flow\n"
        "/stats - Show your statistics for the current week\n"
        "/history - Show your historical weekly statistics"
    )
    await update.message.reply_text(help_text)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new task."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check for duplicate command execution
    message_id = update.message.message_id
    if hasattr(context, 'processed_messages') and message_id in context.processed_messages:
        logger.info(f"Duplicate message detected: {message_id}")
        return
    
    # Mark this message as processed
    if not hasattr(context, 'processed_messages'):
        context.processed_messages = set()
    context.processed_messages.add(message_id)
    
    # Check if user can create a task
    result = task_service.can_create_task(user.id, chat.id)
    
    if not result.get('can_create', False):
        await update.message.reply_text(
            f"Sorry, you cannot create a task: {result.get('reason', 'Unknown reason')}"
        )
        return
    
    # Get task description from command arguments
    if not context.args or not ' '.join(context.args).strip():
        await update.message.reply_text(
            "Please provide a task description. Example: /add_task Buy groceries"
        )
        return
    
    description = ' '.join(context.args)
    
    # Create task
    task_id = task_service.create_task(user.id, chat.id, description)
    
    if task_id:
        min_tasks_remaining = result.get('min_tasks_remaining', 0)
        if min_tasks_remaining > 0:
            await update.message.reply_text(
                f"Task created successfully! You need to create at least {min_tasks_remaining} more task(s) this week."
            )
        else:
            await update.message.reply_text("Task created successfully!")
    else:
        await update.message.reply_text("Failed to create task. Please try again later.")

async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's tasks for the current week with inline buttons to update status."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Get tasks for current week
    tasks = task_service.get_user_tasks(user.id, chat.id)
    
    if not tasks:
        await update.message.reply_text("You don't have any tasks for this week.")
        return
    
    # Format tasks
    tasks_text = "Your tasks for this week:\n\n"
    for i, task in enumerate(tasks, 1):
        status_emoji = "🆕" if task.status == config.TASK_STATUS['CREATED'] else "✅" if task.status == config.TASK_STATUS['COMPLETED'] else "❌"
        tasks_text += f"{i}. {status_emoji} {task.description} (ID: {task.task_id})\n"
    
    # Create inline keyboard with buttons for each task
    keyboard = []
    for task in tasks:
        task_text = f"{task.description[:30]}..." if len(task.description) > 30 else task.description
        keyboard.append([InlineKeyboardButton(task_text, callback_data=f"select_task:{task.task_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        tasks_text + "\nSelect a task to update its status:",
        reply_markup=reply_markup
    )

async def update_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update a task's status."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Please provide a task ID and status. Example: /update_task 1 completed"
        )
        return
    
    try:
        task_id = int(context.args[0])
        status = context.args[1].lower()
    except (ValueError, IndexError):
        await update.message.reply_text("Invalid task ID or status.")
        return
    
    # Validate status
    if status not in config.TASK_STATUS.values():
        valid_statuses = ", ".join(config.TASK_STATUS.values())
        await update.message.reply_text(f"Invalid status. Valid statuses are: {valid_statuses}")
        return
    
    # Update task status
    success = task_service.update_task_status(task_id, status)
    
    if success:
        await update.message.reply_text(f"Task status updated to {status}.")
    else:
        await update.message.reply_text("Failed to update task status. Please check the task ID and try again.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's statistics for the current week."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Get task statistics
    stats = task_service.get_task_stats(user.id, chat.id)
    
    if not stats:
        await update.message.reply_text("Failed to get statistics. Please try again later.")
        return
    
    # Format statistics
    stats_text = "Your task statistics for this week:\n\n"
    stats_text += f"Total tasks: {stats['total_tasks']}/{stats['max_tasks']}\n"
    stats_text += f"Completed tasks: {stats['completed_tasks']}\n"
    stats_text += f"Canceled tasks: {stats['canceled_tasks']}\n"
    stats_text += f"Pending tasks: {stats['created_tasks']}\n"
    stats_text += f"Completion rate: {stats['completion_rate'] * 100:.1f}%\n"
    
    if stats['total_tasks'] < stats['min_tasks']:
        remaining = stats['min_tasks'] - stats['total_tasks']
        stats_text += f"\nYou need to create at least {remaining} more task(s) this week."
    
    await update.message.reply_text(stats_text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks."""
    query = update.callback_query
    
    # Check if this callback query has already been processed
    if hasattr(context, 'processed_callback_queries') and query.id in context.processed_callback_queries:
        await query.answer("This action has already been processed.")
        return
    
    # Mark this callback query as processed
    if not hasattr(context, 'processed_callback_queries'):
        context.processed_callback_queries = set()
    context.processed_callback_queries.add(query.id)
    
    await query.answer()
    
    # Get callback data
    data = query.data
    
    if data.startswith("select_task:"):
        # Extract task ID
        task_id = int(data.split(":")[1])
        
        # Get task
        task = task_service.get_task(task_id)
        if not task:
            await query.edit_message_text(f"Task {task_id} not found.")
            return
        
        # Show task details and status options
        task_text = f"Task: {task.description}\nCurrent status: {task.status}\n\nSelect new status:"
        
        # Create inline keyboard with status options
        keyboard = []
        for status in config.TASK_STATUS.values():
            if status != task.status:  # Don't show current status as an option
                keyboard.append([InlineKeyboardButton(
                    f"Mark as {status}",
                    callback_data=f"update_status:{task_id}:{status}"
                )])
        
        # Add delete button
        keyboard.append([InlineKeyboardButton("🗑️ Delete task", callback_data=f"delete_task:{task_id}")])
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=task_text,
            reply_markup=reply_markup
        )
    
    elif data.startswith("update_status:"):
        # Extract task ID and new status
        parts = data.split(":")
        task_id = int(parts[1])
        new_status = parts[2]
        
        # Update task status
        success = task_service.update_task_status(task_id, new_status)
        
        if success:
            await query.edit_message_text(f"Task {task_id} status updated to {new_status}.")
        else:
            await query.edit_message_text(f"Failed to update task {task_id} status.")
    
    elif data.startswith("delete_task:"):
        # Extract task ID
        task_id = int(data.split(":")[1])
        
        # Delete task
        success = task_service.delete_task(task_id)
        
        if success:
            await query.edit_message_text(f"Task {task_id} has been deleted.")
        else:
            await query.edit_message_text(f"Failed to delete task {task_id}.")
    
    elif data == "cancel":
        # Get user and chat
        user = update.effective_user
        chat = update.callback_query.message.chat
        
        # Get tasks for current week
        tasks = task_service.get_user_tasks(user.id, chat.id)
        
        if not tasks:
            await query.edit_message_text("You don't have any tasks for this week.")
            return
        
        # Format tasks
        tasks_text = "Your tasks for this week:\n\n"
        for i, task in enumerate(tasks, 1):
            status_emoji = "🆕" if task.status == config.TASK_STATUS['CREATED'] else "✅" if task.status == config.TASK_STATUS['COMPLETED'] else "❌"
            tasks_text += f"{i}. {status_emoji} {task.description} (ID: {task.task_id})\n"
        
        # Create inline keyboard with buttons for each task
        keyboard = []
        for task in tasks:
            task_text = f"{task.description[:30]}..." if len(task.description) > 30 else task.description
            keyboard.append([InlineKeyboardButton(task_text, callback_data=f"select_task:{task.task_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            tasks_text + "\nSelect a task to update its status:",
            reply_markup=reply_markup
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(f"Error: {context.error} caused by {update}")
    
    # Check if this is an edited message error
    if update and hasattr(update, 'edited_message') and update.edited_message:
        # We don't need to respond to edited messages
        return
    
    # For other errors, try to reply if possible
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's historical weekly statistics."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Get weekly stats from database (limit to last 10 weeks)
    weekly_stats = db_manager.get_user_stats_history_in_chat(user.id, chat.id, limit=10)
    
    if not weekly_stats:
        await update.message.reply_text("You don't have any historical statistics yet.")
        return
    
    # Format statistics
    history_text = "Your historical weekly statistics:\n\n"
    
    for stat in weekly_stats:
        history_text += f"Week {stat.week_number}, {stat.year}:\n"
        history_text += f"  Total tasks: {stat.tasks_created}\n"
        history_text += f"  Completed: {stat.tasks_completed}\n"
        history_text += f"  Canceled: {stat.tasks_canceled}\n"
        history_text += f"  Completion rate: {stat.completion_rate * 100:.1f}%\n\n"
    
    await update.message.reply_text(history_text)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(config.TELEGRAM_API_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_task", add_task))
    application.add_handler(CommandHandler("my_tasks", my_tasks))
    application.add_handler(CommandHandler("update_task", update_task_status))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("history", history))

    # Register callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Register conversation handlers
    application.add_handler(conversation_handlers.get_add_task_handler())
    application.add_handler(conversation_handlers.get_update_task_handler())
    
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