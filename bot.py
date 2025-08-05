#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Task Management Bot
A bot that helps users manage their weekly tasks.
"""

import logging
import sys
import json
import datetime
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

import config
from database import DatabaseManager
from services import UserService, TaskService, StatisticsService
from handlers import ConversationHandlers
from utils import TaskScheduler

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
statistics_service = StatisticsService(db_manager)

# Initialize conversation handlers
conversation_handlers = ConversationHandlers(task_service, user_service)

# Initialize scheduler
scheduler = TaskScheduler()

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
        "/stats_chat - Show completion rates for all users in the chat\n"
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
    
    # Get page number from context or use default
    page = 1
    if context.user_data and 'task_page' in context.user_data:
        page = context.user_data['task_page']
    
    # Handle page navigation from callback
    if update.callback_query and update.callback_query.data.startswith("page:"):
        page = int(update.callback_query.data.split(":")[1])
        if context.user_data is not None:
            # Use direct assignment for individual keys
            context.user_data['task_page'] = page
        else:
            logger.warning("user_data is None, cannot store page number")
        await update.callback_query.answer()
    
    # Calculate pagination
    items_per_page = 5  # Standard number of items per page
    total_pages = (len(tasks) + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))  # Ensure page is within valid range
    
    # Debug logging
    logger.info(f"Tasks pagination: {len(tasks)} tasks, {items_per_page} per page, {total_pages} total pages, current page {page}")
    
    # Get tasks for current page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(tasks))
    current_page_tasks = tasks[start_idx:end_idx]
    
    # Format tasks
    tasks_text = f"Your tasks for this week (Page {page}/{total_pages}):\n\n"
    for i, task in enumerate(current_page_tasks, start_idx + 1):
        status_emoji = "🆕" if task.status == config.TASK_STATUS['CREATED'] else "✅" if task.status == config.TASK_STATUS['COMPLETED'] else "❌"
        tasks_text += f"{i}. {status_emoji} {task.description}\n"
    
    # Create inline keyboard with buttons for each task
    keyboard = []
    for task in current_page_tasks:
        task_text = f"{task.description[:30]}..." if len(task.description) > 30 else task.description
        keyboard.append([InlineKeyboardButton(task_text, callback_data=f"select_task:{task.task_id}")])
    
    # Add pagination navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"page:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"page:{page+1}"))
    
    # Always add navigation buttons if there are multiple pages
    if total_pages > 1:
        keyboard.append(nav_buttons)
        logger.info(f"Adding pagination buttons: {nav_buttons}")
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message based on context
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=tasks_text + "\nSelect a task to update its status:",
            reply_markup=reply_markup
        )
    else:
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
    
    # Generate current statistics for the user
    now = datetime.datetime.now()
    week_number = now.isocalendar()[1]
    year = now.year
    
    # Ensure we have the latest statistics
    statistics_service.generate_weekly_stats_for_chat(chat.id)
    
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

async def stats_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics for all users in the chat with pagination."""
    chat = update.effective_chat
    
    # Generate current statistics for the chat
    statistics_service.generate_weekly_stats_for_chat(chat.id)
    
    # Get chat completion rates
    completion_rates = statistics_service.get_chat_users_completion_rates(chat.id)
    
    if not completion_rates:
        await update.message.reply_text("No statistics available for this chat.")
        return
    
    # Get page number from context or use default
    page = context.user_data.get('stats_chat_page', 1) if context.user_data else 1
    
    # Handle page navigation from callback
    if update.callback_query and update.callback_query.data.startswith("stats_chat_page:"):
        page = int(update.callback_query.data.split(":")[1])
        if context.user_data is not None:
            context.user_data['stats_chat_page'] = page
        else:
            logger.warning("user_data is None, cannot store page number")
        await update.callback_query.answer()
    
    # Calculate pagination
    items_per_page = 5  # Show 5 users per page
    total_pages = (len(completion_rates) + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))  # Ensure page is within valid range
    
    # Get stats for current page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(completion_rates))
    current_page_rates = completion_rates[start_idx:end_idx]
    
    # Format statistics
    now = datetime.datetime.now()
    week_number = now.isocalendar()[1]
    year = now.year
    
    stats_text = f"📊 Chat Completion Rates (Week {week_number}, {year}) - Page {page}/{total_pages}:\n\n"
    
    for _, username, completion_rate in current_page_rates:
        stats_text += f"{username}: {completion_rate * 100:.1f}%\n"
    
    # Create pagination navigation buttons
    keyboard = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"stats_chat_page:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"stats_chat_page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        reply_markup = None
    
    # Send or edit message based on context
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=stats_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup
        )

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
            await query.edit_message_text("Task not found.")
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
            await query.edit_message_text(f"Task status updated to {new_status}.")
        else:
            await query.edit_message_text("Failed to update task status.")
    
    elif data.startswith("delete_task:"):
        # Extract task ID
        task_id = int(data.split(":")[1])
        
        # Delete task
        success = task_service.delete_task(task_id)
        
        if success:
            await query.edit_message_text("Task has been deleted.")
        else:
            await query.edit_message_text("Failed to delete task.")
    
    elif data == "cancel":
        # Return to task list with pagination
        await my_tasks(update, context)
    
    elif data.startswith("page:"):
        # Handle pagination in my_tasks function
        # Extract page number and store it in context
        page = int(data.split(":")[1])
        if context.user_data is not None:
            # Use direct assignment for individual keys
            context.user_data['task_page'] = page
        else:
            logger.warning("user_data is None, cannot store page number")
        await my_tasks(update, context)
    
    elif data.startswith("history_page:"):
        # Handle pagination in history function
        await history(update, context)
    
    elif data.startswith("stats_chat_page:"):
        # Handle pagination in stats_chat function
        await stats_chat(update, context)

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
    """Show user's historical weekly statistics with pagination."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Get weekly stats from database (get more for pagination)
    weekly_stats = db_manager.get_user_stats_history_in_chat(user.id, chat.id, limit=50)
    
    if not weekly_stats:
        await update.message.reply_text("You don't have any historical statistics yet.")
        return
    
    # Get page number from context or use default
    page = context.user_data.get('history_page', 1) if context.user_data else 1
    
    # Handle page navigation from callback
    if update.callback_query and update.callback_query.data.startswith("history_page:"):
        page = int(update.callback_query.data.split(":")[1])
        if context.user_data is not None:
            context.user_data['history_page'] = page
        else:
            logger.warning("user_data is None, cannot store page number")
        await update.callback_query.answer()
    
    # Calculate pagination
    items_per_page = 3  # Show 3 weeks per page
    total_pages = (len(weekly_stats) + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))  # Ensure page is within valid range
    
    # Get stats for current page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(weekly_stats))
    current_page_stats = weekly_stats[start_idx:end_idx]
    
    # Format statistics
    history_text = f"Your historical weekly statistics (Page {page}/{total_pages}):\n\n"
    
    for stat in current_page_stats:
        history_text += f"Week {stat.week_number}, {stat.year}:\n"
        history_text += f"  Total tasks: {stat.tasks_created}\n"
        history_text += f"  Completed: {stat.tasks_completed}\n"
        history_text += f"  Canceled: {stat.tasks_canceled}\n"
        history_text += f"  Completion rate: {stat.completion_rate * 100:.1f}%\n\n"
    
    # Create pagination navigation buttons
    keyboard = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"history_page:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"history_page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        reply_markup = None
    
    # Send or edit message based on context
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=history_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            history_text,
            reply_markup=reply_markup
        )

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
    application.add_handler(CommandHandler("stats_chat", stats_chat))
    application.add_handler(CommandHandler("history", history))

    # Register callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Register conversation handlers
    application.add_handler(conversation_handlers.get_add_task_handler())
    application.add_handler(conversation_handlers.get_update_task_handler())
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Set up scheduler
    scheduler.schedule_weekly_task_reset(statistics_service.reset_weekly_tasks)
    scheduler.schedule_weekly_stats_generation(lambda: statistics_service.generate_weekly_stats_for_all_chats())
    scheduler.start()
    logger.info("Scheduler started")
    
    # Set up commands menu
    from telegram import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
    
    # Commands for all chats
    common_commands = [
        ("start", "Start the bot and register as a user"),
        ("help", "Show help message"),
        ("add_task", "Add a new task for the current week"),
        ("add_task_conv", "Add a new task using conversation flow"),
        ("my_tasks", "Show your tasks for the current week"),
        ("update_task", "Update the status of a task"),
        ("update_task_conv", "Update task status using conversation flow"),
        ("stats", "Show your statistics for the current week"),
        ("history", "Show your historical weekly statistics")
    ]
    
    # Additional commands for group chats
    group_commands = common_commands + [
        ("stats_chat", "Show completion rates for all users in the chat")
    ]
    
    # We'll set up commands when the bot starts
    application.job_queue.run_once(
        lambda context: context.application.create_task(async_setup_commands(context.application)),
        when=0
    )
    
    async def async_setup_commands(app):
        # Set default commands for all chats
        await app.bot.set_my_commands(
            [BotCommand(command, description) for command, description in common_commands]
        )
        
        # Set specific commands for private chats
        await app.bot.set_my_commands(
            [BotCommand(command, description) for command, description in common_commands],
            scope=BotCommandScopeAllPrivateChats()
        )
        
        # Set specific commands for group chats
        await app.bot.set_my_commands(
            [BotCommand(command, description) for command, description in group_commands],
            scope=BotCommandScopeAllGroupChats()
        )
        
        logger.info("Command menus set up for different chat types")

    # Start the Bot
    application.run_polling()
    logger.info("Bot started")

def shutdown():
    """Shutdown the bot and scheduler."""
    if scheduler.scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        shutdown()
        sys.exit(1)