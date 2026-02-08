#!/bin/bash
#
# GitHub Monitor - Quick Start Script
# Interactive setup for first-time users
#

set -e

echo "======================================"
echo "GitHub Monitor - Quick Start Setup"
echo "======================================"
echo

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.12"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
    echo "❌ Error: Python 3.12+ required (found $PYTHON_VERSION)"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION detected"
echo

# Create config if it doesn't exist
if [ ! -f config.json ]; then
    echo "Creating config.json from template..."
    cp config.json.example config.json
    echo "✓ config.json created"
else
    echo "✓ config.json already exists"
fi
echo

# Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not set"
    echo
    echo "Please set your GitHub token:"
    echo "  export GITHUB_TOKEN='ghp_your_token_here'"
    echo
    echo "Get a token at: https://github.com/settings/tokens"
    echo "Required scope: repo"
    echo
    read -p "Press Enter after setting GITHUB_TOKEN, or Ctrl+C to exit..."

    if [ -z "$GITHUB_TOKEN" ]; then
        echo "❌ GITHUB_TOKEN still not set. Exiting."
        exit 1
    fi
fi
echo "✓ GITHUB_TOKEN configured"
echo

# Test GitHub API connectivity
echo "Testing GitHub API connectivity..."
if python3 -c "
from github_client import GitHubClient
import os
client = GitHubClient(os.environ['GITHUB_TOKEN'])
user = client.get_authenticated_user()
print(f'✓ Connected as: {user[\"login\"]}')
" 2>/dev/null; then
    echo
else
    echo "❌ GitHub API test failed"
    echo "Check your token and network connectivity"
    exit 1
fi

# Ask about Telegram
echo "Configure Telegram notifications? (optional)"
read -p "Enable Telegram? [y/N]: " ENABLE_TELEGRAM
echo

if [[ "$ENABLE_TELEGRAM" =~ ^[Yy]$ ]]; then
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        echo "Get your bot token from: https://t.me/botfather"
        read -p "Enter TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
        export TELEGRAM_BOT_TOKEN
    fi

    if [ -z "$TELEGRAM_CHAT_ID" ]; then
        echo "Get your chat ID from: https://t.me/userinfobot"
        read -p "Enter TELEGRAM_CHAT_ID: " TELEGRAM_CHAT_ID
        export TELEGRAM_CHAT_ID
    fi

    echo "Testing Telegram connection..."
    if python3 test_telegram.py 2>/dev/null; then
        echo "✓ Telegram configured successfully"
    else
        echo "⚠️  Telegram test failed (continuing anyway)"
    fi
else
    echo "Skipping Telegram configuration"
fi
echo

# Run end-to-end test
echo "Running end-to-end test..."
echo
if python3 test_e2e.py; then
    echo
    echo "======================================"
    echo "✅ Setup Complete!"
    echo "======================================"
    echo
    echo "Next steps:"
    echo
    echo "1. Run a manual check:"
    echo "   ./monitor_check.py"
    echo
    echo "2. Install as cron job (runs every 20 min):"
    echo "   ./install_cron.sh"
    echo
    echo "3. Run continuous monitoring:"
    echo "   ./run_monitor_loop.py"
    echo
    echo "4. Deploy with Docker:"
    echo "   docker-compose up -d"
    echo
    echo "See DEPLOY.md for more deployment options."
    echo
else
    echo
    echo "⚠️  End-to-end test failed"
    echo "Check logs above for errors"
    exit 1
fi
