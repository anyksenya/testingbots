# Use Python 3.9 as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only Python files and .env file
COPY *.py ./
COPY .env ./
COPY handlers/*.py ./handlers/
COPY services/*.py ./services/
COPY database/*.py ./database/
COPY utils/*.py ./utils/

# Create necessary directories
RUN mkdir -p data

# Create a volume for the database
VOLUME /app/data

# Run the bot
CMD ["python", "bot.py"]