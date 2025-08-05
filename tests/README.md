# Telegram Task Bot Tests

This directory contains tests for the Telegram Task Bot. The tests are organized into several files:

- `test_plan.md`: A comprehensive test plan outlining all test cases for the bot
- `test_database.py`: Tests for the database manager
- `test_services.py`: Tests for the service layer (UserService, TaskService, StatisticsService)
- `test_scheduler.py`: Tests for the scheduler functionality
- `run_tests.py`: Script to run all tests

## Running the Tests

You can run all tests using the `run_tests.py` script:

```bash
python tests/run_tests.py
```

Or you can run individual test files:

```bash
python tests/test_database.py
python tests/test_services.py
python tests/test_scheduler.py
```

## Test Coverage

The tests cover the following components:

1. **Database Manager**:
   - Creating, retrieving, updating, and deleting users
   - Creating, retrieving, and updating chats
   - Creating and retrieving user-chat relationships
   - Creating, retrieving, updating, and deleting tasks
   - Creating and retrieving weekly statistics

2. **Services**:
   - User registration and management
   - Task creation, retrieval, updating, and deletion
   - Statistics generation and retrieval

3. **Scheduler**:
   - Scheduling weekly task resets
   - Scheduling weekly statistics generation
   - Integration with the statistics service

## Manual Testing

For components that interact with the Telegram API, manual testing is required. The `test_plan.md` file contains a comprehensive list of test cases that should be executed manually.

## Adding New Tests

When adding new functionality to the bot, you should also add corresponding tests. Follow these guidelines:

1. Add unit tests for new database operations in `test_database.py`
2. Add unit tests for new service methods in `test_services.py`
3. Add unit tests for new scheduler functionality in `test_scheduler.py`
4. Add new test cases to the test plan in `test_plan.md`

## Debugging

If a test fails, you can run it with increased verbosity to get more information:

```bash
python tests/test_database.py -v
```

You can also run a specific test case:

```bash
python tests/test_database.py TestDatabaseManager.test_create_and_get_user