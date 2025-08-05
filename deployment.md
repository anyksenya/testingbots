# Telegram Task Bot Deployment Guide

This document provides instructions for deploying the Telegram Task Bot to a production environment.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- A server or hosting platform (e.g., VPS, AWS, Heroku, PythonAnywhere)
- A Telegram Bot API token (obtained from BotFather)

## Deployment Steps

### 1. Set Up the Server

1. **Provision a server** with your preferred hosting provider.
2. **Install Python 3.9+** if not already installed:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```
3. **Create a directory** for the bot:
   ```bash
   mkdir -p /opt/telegram-task-bot
   cd /opt/telegram-task-bot
   ```

### 2. Clone or Upload the Code

Either clone the repository or upload the code to the server:

```bash
# Option 1: Clone from repository
git clone <repository-url> .

# Option 2: Upload files using SCP or SFTP
scp -r /path/to/local/project/* user@server:/opt/telegram-task-bot/
```

### 3. Set Up Virtual Environment

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file with the necessary configuration:

```bash
cp .env.example .env
nano .env
```

Update the following variables:
- `TELEGRAM_API_TOKEN`: Your Telegram Bot API token
- `DATABASE_PATH`: Path to the SQLite database (e.g., `sqlite:///data/taskbot.db`)
- `LOG_LEVEL`: Set to `INFO` or `WARNING` for production
- `TIMEZONE`: Your preferred timezone (e.g., `Europe/Moscow`)

### 6. Set Up Database Directory

Create the directory for the database:

```bash
mkdir -p data
```

### 7. Set Up Logging

Create a directory for logs:

```bash
mkdir -p logs
```

Update the logging configuration in `config.py` to write logs to a file:

```python
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
```

### 8. Set Up Systemd Service (Linux)

Create a systemd service file to run the bot as a service:

```bash
sudo nano /etc/systemd/system/telegram-task-bot.service
```

Add the following content:

```ini
[Unit]
Description=Telegram Task Bot
After=network.target

[Service]
User=<your-user>
Group=<your-group>
WorkingDirectory=/opt/telegram-task-bot
ExecStart=/opt/telegram-task-bot/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=telegram-task-bot
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-task-bot
sudo systemctl start telegram-task-bot
```

### 9. Set Up Database Backup

Create a backup script:

```bash
nano backup.sh
```

Add the following content:

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR=/opt/telegram-task-bot/backups
mkdir -p $BACKUP_DIR
cp /opt/telegram-task-bot/data/taskbot.db $BACKUP_DIR/taskbot_$DATE.db
# Keep only the last 7 backups
ls -t $BACKUP_DIR/taskbot_*.db | tail -n +8 | xargs rm -f
```

Make the script executable:

```bash
chmod +x backup.sh
```

Set up a cron job to run the backup script daily:

```bash
crontab -e
```

Add the following line:

```
0 0 * * * /opt/telegram-task-bot/backup.sh
```

### 10. Set Up Monitoring

#### Option 1: Basic Monitoring with Systemd

Check the status of the bot:

```bash
sudo systemctl status telegram-task-bot
```

View logs:

```bash
sudo journalctl -u telegram-task-bot
```

#### Option 2: Advanced Monitoring with Prometheus and Grafana

For more advanced monitoring, you can set up Prometheus and Grafana. This is beyond the scope of this guide, but there are many resources available online.

### 11. Error Reporting

For error reporting, you can use a service like Sentry:

1. Sign up for a free account at [sentry.io](https://sentry.io)
2. Install the Sentry SDK:
   ```bash
   pip install sentry-sdk
   ```
3. Add Sentry to your bot:
   ```python
   import sentry_sdk
   
   sentry_sdk.init(
       dsn="your-sentry-dsn",
       traces_sample_rate=1.0
   )
   ```

### 12. Testing in Production

After deployment, perform the following tests:

1. Start the bot with `/start`
2. Create a task with `/add_task`
3. List tasks with `/my_tasks`
4. Update a task status
5. Check statistics with `/stats`
6. Test in a group chat
7. Test with multiple users

### 13. Maintenance

#### Updating the Bot

To update the bot:

1. Pull the latest changes or upload the new code
2. Restart the service:
   ```bash
   sudo systemctl restart telegram-task-bot
   ```

#### Checking Logs

To check the logs:

```bash
tail -f logs/bot.log
```

#### Database Maintenance

To perform database maintenance:

1. Stop the bot:
   ```bash
   sudo systemctl stop telegram-task-bot
   ```
2. Perform maintenance (e.g., vacuum the database):
   ```bash
   sqlite3 data/taskbot.db "VACUUM;"
   ```
3. Start the bot:
   ```bash
   sudo systemctl start telegram-task-bot
   ```

## Troubleshooting

### Bot Not Responding

1. Check if the bot is running:
   ```bash
   sudo systemctl status telegram-task-bot
   ```
2. Check the logs:
   ```bash
   tail -f logs/bot.log
   ```
3. Restart the bot:
   ```bash
   sudo systemctl restart telegram-task-bot
   ```

### Database Issues

1. Check if the database file exists:
   ```bash
   ls -l data/taskbot.db
   ```
2. Check if the database is not corrupted:
   ```bash
   sqlite3 data/taskbot.db "PRAGMA integrity_check;"
   ```
3. Restore from backup if necessary:
   ```bash
   cp backups/taskbot_<date>.db data/taskbot.db
   ```

## Security Considerations

1. **Secure the server**: Keep the server updated with security patches
2. **Restrict access**: Use a firewall to restrict access to the server
3. **Use HTTPS**: If exposing any web interfaces, use HTTPS
4. **Protect the .env file**: Ensure the .env file is not accessible from the web
5. **Regular backups**: Ensure regular backups are working correctly