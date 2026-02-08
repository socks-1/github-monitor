# GitHub Monitor

A lightweight GitHub monitoring tool that tracks repository activity, issues, and pull requests.

## Features

- **Repository Summary**: View your recent repositories sorted by last push
- **Activity Dashboard**: Aggregate view of issues and PRs across all repos
- **Repository Detail**: Deep dive into a specific repository's open issues and PRs
- **Relative Timestamps**: Human-readable time formats ("2h ago", "3d ago")

## Requirements

- Python 3.12+
- GitHub Personal Access Token with repo scope

## Setup

1. Set your GitHub token as an environment variable:
```bash
export GITHUB_TOKEN=your_token_here
```

2. Make the scripts executable:
```bash
chmod +x monitor.py github_client.py
```

## Usage

### Summary View
Shows your recent repositories with basic stats:
```bash
python3 monitor.py summary
```

### Dashboard View
Aggregates issues and PRs across your repositories:
```bash
python3 monitor.py dashboard
```

### Repository Detail
View detailed information about a specific repository:
```bash
python3 monitor.py repo:owner/name
```

## Examples

```bash
# View recent repositories
python3 monitor.py summary

# See activity dashboard
python3 monitor.py dashboard

# Deep dive into a specific repo
python3 monitor.py repo:anthropics/claude-code
```

## Architecture

- `github_client.py`: Lightweight GitHub API client using urllib
- `monitor.py`: Display layer with multiple view modes

## Automated Monitoring

The monitor now includes persistent storage and change detection:

### Run a one-time check
```bash
python3 monitor_check.py
```

This will:
- Check all watched repositories for new/updated issues and PRs
- Store data in SQLite database
- Queue Telegram notifications (if configured)
- Print a summary of changes

### Install automated monitoring (cron)
```bash
./install_cron.sh
```

This installs a cron job that runs every 20 minutes.

### Configuration

Create `config.json` from the example:
```bash
cp config.json.example config.json
```

Edit `config.json` to customize:
- Repository watchlist
- Telegram settings
- Monitoring interval

### Telegram Notifications

To enable Telegram notifications:

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your chat ID (message [@userinfobot](https://t.me/userinfobot))
3. Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN=your_bot_token
export TELEGRAM_CHAT_ID=your_chat_id
```

### Token Expiry Tracking

To get warnings before your GitHub token expires, set the expiry date:

```bash
export GITHUB_TOKEN_EXPIRES_AT="2026-03-15T00:00:00Z"
```

The monitor will:
- Warn if token expires in ≤30 days
- Alert strongly if token expires in ≤7 days
- Report expired tokens

This helps prevent silent monitoring failures when tokens expire.

## Architecture

- `github_client.py`: Lightweight GitHub API client
- `monitor.py`: Display layer with multiple view modes
- `database.py`: SQLite database for tracking changes
- `monitor_daemon.py`: Change detection logic
- `telegram_notifier.py`: Telegram notification handler
- `monitor_check.py`: Main monitoring script (cron-ready)
