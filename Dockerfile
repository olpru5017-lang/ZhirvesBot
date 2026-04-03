# Discord Music Bot - Docker Image
FROM python:3.10-slim

# Install FFmpeg and other dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Run the bot
CMD ["python", "main.py"]
