# Use a stable Python runtime
FROM python:3.10-slim

# Install system dependencies including FFmpeg
# Note: ImageMagick install hota hai lekin policy.xml ka path verify karke fix karein
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    imagemagick \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick security policy - find and patch whatever path exists
RUN find /etc -name "policy.xml" 2>/dev/null | while read f; do \
      sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/g' "$f" || true; \
    done; \
    echo "ImageMagick policy patched (or not found, that is OK)"

# Set the working directory
WORKDIR /app

# Create data directory for SQLite with correct permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy requirements first (better Docker layer caching)
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

# Start with Gunicorn - production ready
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120", "app:app"]
