"""
Conversation handlers for the Telegram Task Bot.
This module contains conversation handlers for multi-step interactions.
"""

import logging
from typing import Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from telegram.constants import ParseMode

import config
from services import TaskService, UserService

logger = logging.getLogger(__name__)

# Conversation states
TASK_DESCRIPTION = 0
SELECTING_TASK = 1
SELECTING_STATUS = 2

class ConversationHandlers:
    """Class for managing conversation handlers."""
    
    def __init__(self, task_service: TaskService, user_service: UserService):
        """Initialize conversation handlers.
        
        Args:
            task_service: Task service instance
            user_service: User service instance
        """
        self.task_service = task_service
        self.user_service = user_service
    
    def get_add_task_handler(self) -> ConversationHandler:
        """Get conversation handler for adding a task."""
        return ConversationHandler(
            entry_points=[CommandHandler("add_task_conv", self.add_task_start)],
            states={
                TASK_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_task_description)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            name="add_task_conversation",
            persistent=False,
        )
    
    def get_update_task_handler(self) -> ConversationHandler:
        """Get conversation handler for updating a task status."""
        return ConversationHandler(
            entry_points=[CommandHandler("update_task_conv", self.update_task_start)],
            states={
                SELECTING_TASK: [
                    CallbackQueryHandler(self.select_task, pattern=r"^select_task:\d+$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.update_task_id_input)
                ],
                SELECTING_STATUS: [
                    CallbackQueryHandler(self.update_task_status, pattern=r"^update_status:\d+:[a-z]+$")
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel_conversation),
                CallbackQueryHandler(self.cancel_conversation, pattern="^cancel$")
            ],
            name="update_task_conversation",
            persistent=False,
        )
    
    async def add_task_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the add task conversation."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Check if user can create a task
        result = self.task_service.can_create_task(user.id, chat.id)
        
        if not result.get('can_create', False):
            await update.message.reply_text(
                f"Sorry, you cannot create a task: {result.get('reason', 'Unknown reason')}"
            )
            return ConversationHandler.END
        
        await update.message.reply_text(
            "Please enter a description for your task.\n"
            "Send /cancel to cancel the operation."
        )
        
        return TASK_DESCRIPTION
    
    async def add_task_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process the task description."""
        user = update.effective_user
        chat = update.effective_chat
        description = update.message.text
        
        # Create task
        task_id = self.task_service.create_task(user.id, chat.id, description)
        
        if task_id:
            # Check if user needs to create more tasks
            result = self.task_service.can_create_task(user.id, chat.id)
            min_tasks_remaining = result.get('min_tasks_remaining', 0)
            
            if min_tasks_remaining > 0:
                await update.message.reply_text(
                    f"Task created successfully! You need to create at least {min_tasks_remaining} more task(s) this week.\n"
                    f"Would you like to add another task?",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Yes, add another task", callback_data="add_another_task")],
                        [InlineKeyboardButton("No, I'm done for now", callback_data="done_adding_tasks")]
                    ])
                )
                # Store the conversation state in user_data
                context.user_data['awaiting_add_another_task'] = True
                return ConversationHandler.END
            else:
                await update.message.reply_text("Task created successfully!")
        else:
            await update.message.reply_text("Failed to create task. Please try again later.")
        
        return ConversationHandler.END
    
    async def update_task_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the update task conversation."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Get tasks for current week
        tasks = self.task_service.get_user_tasks(user.id, chat.id)
        
        if not tasks:
            await update.message.reply_text("You don't have any tasks for this week.")
            return ConversationHandler.END
        
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
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            tasks_text + "\nSelect a task to update its status or enter a task ID:",
            reply_markup=reply_markup
        )
        
        return SELECTING_TASK
    
    async def update_task_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process task ID input."""
        try:
            task_id = int(update.message.text.strip())
            
            # Get task
            task = self.task_service.get_task(task_id)
            if not task:
                await update.message.reply_text(f"Task {task_id} not found. Please try again.")
                return SELECTING_TASK
            
            # Show task details and status options
            return await self.show_status_options(update, context, task)
            
        except ValueError:
            await update.message.reply_text("Invalid task ID. Please enter a number.")
            return SELECTING_TASK
    
    async def select_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process task selection."""
        query = update.callback_query
        await query.answer()
        
        # Extract task ID
        task_id = int(query.data.split(":")[1])
        
        # Get task
        task = self.task_service.get_task(task_id)
        if not task:
            await query.edit_message_text(f"Task {task_id} not found.")
            return ConversationHandler.END
        
        # Show task details and status options
        return await self.show_status_options(update, context, task, is_callback=True)
    
    async def show_status_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, task, is_callback=False) -> int:
        """Show status options for a task."""
        task_text = f"Task: {task.description}\nCurrent status: {task.status}\n\nSelect new status:"
        
        # Create inline keyboard with status options
        keyboard = []
        for status in config.TASK_STATUS.values():
            if status != task.status:  # Don't show current status as an option
                keyboard.append([InlineKeyboardButton(
                    f"Mark as {status}",
                    callback_data=f"update_status:{task.task_id}:{status}"
                )])
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if is_callback:
            await update.callback_query.edit_message_text(
                text=task_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=task_text,
                reply_markup=reply_markup
            )
        
        return SELECTING_STATUS
    
    async def update_task_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Update task status."""
        query = update.callback_query
        await query.answer()
        
        # Extract task ID and new status
        parts = query.data.split(":")
        task_id = int(parts[1])
        new_status = parts[2]
        
        # Update task status
        success = self.task_service.update_task_status(task_id, new_status)
        
        if success:
            await query.edit_message_text(f"Task {task_id} status updated to {new_status}.")
        else:
            await query.edit_message_text(f"Failed to update task {task_id} status.")
        
        return ConversationHandler.END
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        if update.callback_query:
            await update.callback_query.edit_message_text("Operation canceled.")
        else:
            await update.message.reply_text("Operation canceled.")
        return ConversationHandler.END
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries for conversation-related buttons."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_another_task":
            # Start a new add task conversation
            await query.edit_message_text("Please enter a description for your new task.")
            context.user_data['awaiting_add_another_task'] = False
            context.user_data['in_add_task_conversation'] = True
            
            # We need to manually set the state since we're not using ConversationHandler here
            # The next message will be handled by a message handler that checks this state
        
        elif query.data == "done_adding_tasks":
            await query.edit_message_text("Alright, no more tasks will be added.")
            context.user_data['awaiting_add_another_task'] = False