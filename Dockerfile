# Production Dockerfile for THUMBIFY
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (including ffmpeg and ffprobe)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY app/ app/
COPY assets/ assets/

# Create runtime directories
RUN mkdir -p downloads logs

# Command to execute
CMD ["python", "-m", "app.main"]

