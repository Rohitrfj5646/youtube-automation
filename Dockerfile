# Use a more modern and stable Python runtime
FROM python:3.10-slim

# Install system dependencies, FFmpeg, and ImageMagick
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    imagemagick \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick security policy to allow TextClip
RUN sed -i 's/policy domain="path" rights="none" pattern="@\*"/policy domain="path" rights="read|write" pattern="@\*"/g' /etc/ImageMagick-6/policy.xml

# Set the working directory
WORKDIR /app

# Create data directory for SQLite
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV DB_PATH=/app/data/automation.db
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8080

# Start the application using Gunicorn for production reliability
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "0", "app:app"]
