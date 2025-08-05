# Running the Telegram Task Bot with Docker

This document provides instructions for running the Telegram Task Bot using Docker.

## Prerequisites

- Docker installed on your system
- A Telegram Bot token (obtained from BotFather)

## Setup

1. Create a `.env` file in the project root with the following content:

```
TELEGRAM_API_TOKEN=your_telegram_bot_token_here
DATABASE_PATH=sqlite:///data/taskbot.db
TIMEZONE=Europe/Moscow
```

Replace `your_telegram_bot_token_here` with your actual Telegram Bot token.

2. Build the Docker image:

```bash
docker build -t taskbot .
```

3. Run the Docker container:

```bash
docker run -d --name taskbot -v $(pwd)/data:/app/data taskbot
```

This command:
- Runs the container in detached mode (`-d`)
- Names the container "taskbot" (`--name taskbot`)
- Mounts a volume for persistent database storage (`-v $(pwd)/data:/app/data`)

## Viewing Logs

To view the logs of the running container:

```bash
docker logs -f taskbot
```

## Stopping the Bot

To stop the running container:

```bash
docker stop taskbot
```

## Restarting the Bot

To restart the container:

```bash
docker start taskbot