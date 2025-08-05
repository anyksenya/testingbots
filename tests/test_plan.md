# Telegram Task Bot Test Plan

This document outlines the test cases for the Telegram Task Bot to ensure all functionality works as expected.

## 1. User Registration Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| UR-01 | New user registration | 1. Start bot with /start command<br>2. Check database | User should be registered in the database with correct details |
| UR-02 | Existing user registration | 1. Start bot with /start command for an already registered user | User details should be updated if changed |
| UR-03 | User registration in group chat | 1. Add bot to group chat<br>2. Send /start command | Bot should register both user and chat |
| UR-04 | User registration with missing username | 1. Start bot with user who has no username | User should be registered using first_name and last_name |

## 2. Task Management Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| TM-01 | Add task via command | 1. Send `/add_task Buy groceries`<br>2. Check task list | Task should be added with "created" status |
| TM-02 | Add task via conversation | 1. Send `/add_task_conv`<br>2. Enter task description | Task should be added with "created" status |
| TM-03 | View tasks | 1. Send `/my_tasks`<br>2. Check displayed tasks | All user's tasks for current week should be displayed with pagination |
| TM-04 | Update task status via command | 1. Send `/update_task [id] completed`<br>2. Check task status | Task status should be updated to "completed" |
| TM-05 | Update task status via conversation | 1. Send `/update_task_conv`<br>2. Select task<br>3. Select new status | Task status should be updated to selected status |
| TM-06 | Update task status via inline buttons | 1. Send `/my_tasks`<br>2. Click on a task<br>3. Select new status | Task status should be updated to selected status |
| TM-07 | Delete task | 1. Send `/my_tasks`<br>2. Click on a task<br>3. Click "Delete task" | Task should be deleted from database |
| TM-08 | Task limit enforcement | 1. Add maximum allowed tasks<br>2. Try to add one more | Bot should reject the new task with appropriate message |
| TM-09 | Task pagination | 1. Add more than 5 tasks<br>2. Send `/my_tasks`<br>3. Navigate through pages | Pagination should work correctly showing 5 tasks per page |

## 3. Statistics Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| ST-01 | View personal statistics | 1. Send `/stats` | User's statistics for current week should be displayed |
| ST-02 | View chat statistics | 1. Send `/stats_chat` in a group chat | Statistics for all users in chat should be displayed with pagination |
| ST-03 | View historical statistics | 1. Send `/history` | User's historical statistics should be displayed with pagination |
| ST-04 | Statistics calculation | 1. Add tasks with different statuses<br>2. Send `/stats` | Statistics should correctly reflect task counts and completion rate |
| ST-05 | Statistics pagination | 1. Generate statistics for multiple users/weeks<br>2. Check pagination in stats views | Pagination should work correctly in all statistics views |

## 4. Scheduler Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| SC-01 | Weekly task reset | 1. Manually trigger weekly task reset<br>2. Check tasks | Tasks should be archived and statistics generated |
| SC-02 | Weekly statistics generation | 1. Manually trigger statistics generation<br>2. Check statistics | Statistics should be generated for all active chats |
| SC-03 | Scheduler startup | 1. Start the bot<br>2. Check logs | Scheduler should start and schedule jobs correctly |
| SC-04 | Scheduler shutdown | 1. Stop the bot<br>2. Check logs | Scheduler should shut down gracefully |

## 5. Command Menu Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| CM-01 | Command menu in private chat | 1. Start bot in private chat<br>2. Type "/" | Private chat commands should be displayed |
| CM-02 | Command menu in group chat | 1. Start bot in group chat<br>2. Type "/" | Group chat commands should be displayed |
| CM-03 | Command execution | 1. Select command from menu<br>2. Execute it | Command should execute correctly |

## 6. Error Handling Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| EH-01 | Invalid command arguments | 1. Send command with invalid arguments<br>2. Check response | Bot should respond with helpful error message |
| EH-02 | Database connection error | 1. Simulate database connection error<br>2. Try to use bot | Bot should handle error gracefully and inform user |
| EH-03 | Edited message handling | 1. Send command<br>2. Edit the message | Bot should ignore edited messages |
| EH-04 | Duplicate message handling | 1. Simulate duplicate message<br>2. Check response | Bot should process message only once |

## 7. Edge Case Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| EC-01 | Very long task description | 1. Add task with very long description | Bot should handle it correctly, possibly truncating in displays |
| EC-02 | Special characters in task | 1. Add task with special characters | Bot should handle it correctly |
| EC-03 | Empty task list | 1. Ensure user has no tasks<br>2. Send `/my_tasks` | Bot should inform user they have no tasks |
| EC-04 | No statistics available | 1. Ensure user has no statistics<br>2. Send `/stats` | Bot should inform user they have no statistics |
| EC-05 | Maximum number of tasks | 1. Add maximum allowed number of tasks<br>2. Check task list | All tasks should be displayed correctly with pagination |

## 8. Multi-User Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| MU-01 | Multiple users in same chat | 1. Have multiple users use bot in same chat<br>2. Check task isolation | Each user should only see their own tasks |
| MU-02 | Chat statistics with multiple users | 1. Have multiple users with tasks<br>2. Send `/stats_chat` | Statistics for all users should be displayed correctly |
| MU-03 | Concurrent usage | 1. Have multiple users use bot simultaneously<br>2. Check for errors | Bot should handle concurrent usage without errors |

## 9. Performance Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| PF-01 | Response time | 1. Measure response time for commands | Response time should be acceptable (< 2 seconds) |
| PF-02 | Large data handling | 1. Create large number of tasks/users<br>2. Test bot functionality | Bot should handle large data volumes efficiently |
| PF-03 | Memory usage | 1. Monitor memory usage during operation | Memory usage should remain stable |

## 10. Security Tests

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| SE-01 | User data isolation | 1. Try to access another user's tasks | Bot should prevent access to other users' data |
| SE-02 | Input validation | 1. Try to input malicious data<br>2. Check handling | Bot should validate and sanitize all inputs |
| SE-03 | Error message information disclosure | 1. Cause errors<br>2. Check error messages | Error messages should not disclose sensitive information |