# GitHub Monitor - Usage Guide

## Quick Start

### 1. Set Environment Variables

```bash
export GITHUB_TOKEN="your_github_personal_access_token"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_telegram_chat_id"

# Optional: Track token expiry
export GITHUB_TOKEN_EXPIRES_AT="2026-05-09T00:00:00Z"
```

### 2. Choose Your Monitoring Mode

#### Option A: One-Shot Check (for cron)
Run a single monitoring check and exit:
```bash
python3 monitor_check.py
```

This will:
- Check all watched repositories for changes
- Detect new/updated issues and PRs
- Send Telegram notifications for changes
- Exit cleanly

**Best for:** Cron jobs, scheduled tasks, manual checks

#### Option B: Continuous Loop (for containers/services)
Run monitoring continuously at regular intervals:
```bash
python3 run_monitor_loop.py
```

Default interval: 20 minutes. To customize:
```bash
python3 run_monitor_loop.py 10  # Check every 10 minutes
```

**Best for:** Docker containers, systemd services, long-running processes

#### Option C: Cron Installation
Install as a cron job (checks every 20 minutes):
```bash
./install_cron.sh
```

View logs:
```bash
tail -f monitor.log
```

**Best for:** Traditional servers, VPS, development machines

## Display Modes

### Summary View
View your repositories sorted by last push:
```bash
python3 monitor.py summary
```

### Activity Dashboard
See aggregated activity across repositories:
```bash
python3 monitor.py dashboard
```

### Repository Detail
View detailed info about a specific repository:
```bash
python3 monitor.py repo:owner/repo-name
```

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "github": {
    "token_env": "GITHUB_TOKEN",
    "token_expires_at_env": "GITHUB_TOKEN_EXPIRES_AT",
    "watched_repos": []
  },
  "telegram": {
    "enabled": true,
    "bot_token_env": "TELEGRAM_BOT_TOKEN",
    "chat_id_env": "TELEGRAM_CHAT_ID"
  },
  "monitoring": {
    "auto_watch_user_repos": true,
    "max_repos_to_watch": 20,
    "check_interval_minutes": 20
  }
}
```

### Configuration Priority

The monitor uses this priority order:
1. **Database** - Repos you've already watched
2. **Config file** - Explicit `watched_repos` list
3. **Auto-discovery** - Your GitHub repos (if `auto_watch_user_repos: true`)

### Watching Specific Repositories

To monitor only specific repos, edit `config.json`:

```json
{
  "github": {
    "watched_repos": [
      "torvalds/linux",
      "facebook/react",
      "your-org/your-repo"
    ]
  },
  "monitoring": {
    "auto_watch_user_repos": false
  }
}
```

## Testing

### Test GitHub API Connection
```bash
python3 github_client.py
```

### Test Telegram Notifications
```bash
python3 test_telegram.py
```

### Run Integration Tests
```bash
python3 test_integration.py
```

### Run End-to-End Tests
```bash
python3 test_e2e.py
```

## Notification Format

Notifications are sent to Telegram with HTML formatting:

**New Issue Example:**
```
🆕 New Issue
owner/repo#123
Add support for dark mode
View on GitHub
```

**PR Update Example:**
```
📝 PR Updated
owner/repo#456
Fix authentication bug
View on GitHub
```

## Database

The monitor uses SQLite (`github_monitor.db`) to track:
- Repository metadata
- Issues and their states
- Pull requests and their states
- Notification queue and delivery status

### Database Schema

```sql
-- Repositories being monitored
CREATE TABLE repositories (...)

-- Issues and PRs tracked
CREATE TABLE issues (...)
CREATE TABLE pull_requests (...)

-- Notification queue
CREATE TABLE notifications (...)
```

### Inspect Database
```bash
sqlite3 github_monitor.db "SELECT * FROM repositories"
sqlite3 github_monitor.db "SELECT * FROM notifications WHERE sent_at IS NULL"
```

## Troubleshooting

### No Changes Detected
- First run initializes the database with current state
- Changes will be detected on subsequent runs
- Wait for actual GitHub activity to trigger notifications

### Telegram Not Sending
Check credentials:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
python3 test_telegram.py
```

### Token Expiry Warnings
Set the expiry date:
```bash
export GITHUB_TOKEN_EXPIRES_AT="2026-05-09T00:00:00Z"
```

### Database Issues
Reset the database:
```bash
rm github_monitor.db
python3 monitor_check.py  # Reinitialize
```

## Advanced Usage

### Docker Deployment
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
CMD ["python3", "run_monitor_loop.py"]
```

### Systemd Service
Create `/etc/systemd/system/github-monitor.service`:
```ini
[Unit]
Description=GitHub Monitor
After=network.target

[Service]
Type=simple
User=socks
WorkingDirectory=/path/to/github-monitor
Environment=GITHUB_TOKEN=...
Environment=TELEGRAM_BOT_TOKEN=...
Environment=TELEGRAM_CHAT_ID=...
ExecStart=/usr/bin/python3 run_monitor_loop.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable github-monitor
sudo systemctl start github-monitor
sudo systemctl status github-monitor
```

## Security Notes

- Never commit tokens to git (use `.gitignore`)
- Use environment variables for all credentials
- Rotate GitHub tokens regularly (check expiry warnings)
- Keep Telegram bot token secure

## Performance

- Default check interval: 20 minutes
- API rate limit: 5000 requests/hour (authenticated)
- Each check uses ~1-2 API calls per repository
- Database is lightweight (SQLite, local file)

## Support

For issues or questions:
- Check `test_*.py` files for examples
- Review `monitor.log` for errors
- Verify environment variables are set
- Test components individually before full deployment
