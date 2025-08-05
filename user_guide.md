# Telegram Task Bot User Guide

Welcome to the Telegram Task Bot! This guide will help you understand how to use the bot to manage your weekly tasks.

## Getting Started

### Starting the Bot

1. Search for the bot in Telegram by its username
2. Start a conversation with the bot by clicking the "Start" button or sending the `/start` command
3. The bot will register you and send a welcome message

### Available Commands

The bot supports the following commands:

- `/start` - Start the bot and register as a user
- `/help` - Show the help message with available commands
- `/add_task` - Add a new task for the current week
- `/add_task_conv` - Add a new task using conversation flow
- `/my_tasks` - Show your tasks for the current week
- `/update_task` - Update the status of a task
- `/update_task_conv` - Update task status using conversation flow
- `/stats` - Show your statistics for the current week
- `/stats_chat` - Show completion rates for all users in the chat (group chats only)
- `/history` - Show your historical weekly statistics

## Managing Tasks

### Adding Tasks

You can add tasks in two ways:

#### Method 1: Using the `/add_task` command

Send the command followed by the task description:

```
/add_task Buy groceries
```

#### Method 2: Using the conversation flow

1. Send the `/add_task_conv` command
2. The bot will ask you to enter a task description
3. Send your task description as a message

**Note:** You can add between 3 and 5 tasks per week. The bot will inform you if you've reached the minimum or maximum limit.

### Viewing Tasks

To view your current tasks, send the `/my_tasks` command. The bot will display a list of your tasks for the current week with their status:

- 🆕 - Created (not yet completed)
- ✅ - Completed
- ❌ - Canceled

If you have many tasks, they will be displayed with pagination. Use the "Previous" and "Next" buttons to navigate between pages.

### Updating Task Status

You can update task status in three ways:

#### Method 1: From the task list

1. Send the `/my_tasks` command
2. Click on the task you want to update
3. Select the new status from the options provided

#### Method 2: Using the `/update_task` command

Send the command followed by the task number and the new status:

```
/update_task 1 completed
```

Valid statuses are: `created`, `completed`, and `canceled`.

#### Method 3: Using the conversation flow

1. Send the `/update_task_conv` command
2. The bot will show your tasks
3. Select the task you want to update
4. Select the new status from the options provided

### Deleting Tasks

To delete a task:

1. Send the `/my_tasks` command
2. Click on the task you want to delete
3. Click the "🗑️ Delete task" button

## Statistics

### Personal Statistics

To view your personal statistics for the current week, send the `/stats` command. The bot will display:

- Total tasks
- Completed tasks
- Canceled tasks
- Pending tasks
- Completion rate

### Chat Statistics

In group chats, you can view statistics for all users by sending the `/stats_chat` command. This shows the completion rates for all users in the chat.

If there are many users, they will be displayed with pagination. Use the "Previous" and "Next" buttons to navigate between pages.

### Historical Statistics

To view your historical statistics, send the `/history` command. The bot will display your statistics for previous weeks.

If you have statistics for many weeks, they will be displayed with pagination. Use the "Previous" and "Next" buttons to navigate between pages.

## Weekly Reset

The bot automatically resets tasks every Monday at 00:00 UTC+3. This means:

1. Your tasks from the previous week are archived
2. You can start adding new tasks for the new week
3. Your statistics for the previous week are saved and can be viewed with the `/history` command

## Weekly Statistics Generation

Every Friday at 17:00 UTC+3, the bot generates statistics for the current week. This helps you track your progress and see how well you're doing with your tasks.

## Using the Bot in Group Chats

The bot can be used in group chats to track tasks for multiple users:

1. Add the bot to a group chat
2. Each user should send the `/start` command to register
3. Users can manage their own tasks using the commands described above
4. Use the `/stats_chat` command to see completion rates for all users in the chat

## Tips and Best Practices

1. **Create meaningful tasks**: Be specific about what you want to accomplish
2. **Update task status regularly**: Keep your task list up to date
3. **Review your statistics**: Use the statistics to track your progress and improve
4. **Use the bot in group chats**: Encourage accountability by tracking tasks with friends or colleagues
5. **Check your history**: Review your performance over time to identify patterns

## Troubleshooting

### Bot Not Responding

If the bot doesn't respond to your commands:

1. Make sure you're sending the command correctly (with a forward slash)
2. Try sending the `/start` command again
3. Check if Telegram is experiencing issues
4. Contact the bot administrator if the problem persists

### Task Not Appearing

If your task doesn't appear after adding it:

1. Check if you've reached the maximum number of tasks for the week
2. Try adding the task again
3. Contact the bot administrator if the problem persists

### Other Issues

For any other issues, contact the bot administrator with a description of the problem and any error messages you received.