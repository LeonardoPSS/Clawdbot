# Base Image with Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright and X11 (if needed)
# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xauth \
    xvfb \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy source code
COPY . .

# Set Environment Variables
ENV HEADLESS_MODE=true
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the bot (Using the standalone telegram script for stability)
CMD ["python", "run_telegram_bot.py"]
