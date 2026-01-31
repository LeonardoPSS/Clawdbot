# Use official Playwright image with Python 3.10
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install browsers and dependencies
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Ensure directories exist for persistence
RUN mkdir -p browser_profile data assets

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the bot
CMD ["python", "-m", "src.main"]
