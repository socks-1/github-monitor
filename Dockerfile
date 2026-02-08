FROM python:3.12-slim

LABEL maintainer="socks"
LABEL description="GitHub Monitor - Lightweight repository monitoring tool"

WORKDIR /app

# Copy application files
COPY *.py ./
COPY config.json.example ./config.json

# Create directory for database
RUN mkdir -p /data

# Set environment variables
ENV GITHUB_TOKEN=""
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""
ENV GITHUB_TOKEN_EXPIRES_AT=""

# No external dependencies needed - pure Python stdlib!
# Verify Python version
RUN python3 --version

# Make scripts executable
RUN chmod +x *.py

# Health check
HEALTHCHECK --interval=5m --timeout=3s \
  CMD python3 -c "import sqlite3; sqlite3.connect('/data/github_monitor.db').execute('SELECT 1')" || exit 1

# Run continuous monitoring loop by default
CMD ["python3", "run_monitor_loop.py"]
