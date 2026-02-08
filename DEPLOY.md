# GitHub Monitor - Deployment Guide

This guide covers different deployment scenarios for github-monitor.

## Quick Start (Local Development)

1. **Clone and setup**:
```bash
cd ~/workspace/PROJECTS/github-monitor
cp config.json.example config.json
```

2. **Configure environment variables**:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
export TELEGRAM_BOT_TOKEN="your_bot_token"  # Optional
export TELEGRAM_CHAT_ID="your_chat_id"      # Optional
export GITHUB_TOKEN_EXPIRES_AT="2026-03-15T00:00:00Z"  # Optional
```

3. **Test the setup**:
```bash
python3 test_e2e.py
```

4. **Run a check**:
```bash
python3 monitor_check.py
```

## Deployment Option 1: Cron Job (Recommended for VPS/Linux)

**Best for**: Personal servers, VPS, always-on Linux machines

1. **Configure watched repositories** in `config.json`:
```json
{
  "watched_repos": ["owner/repo1", "owner/repo2"],
  "auto_watch_user_repos": true,
  "check_interval_minutes": 20
}
```

2. **Install cron job**:
```bash
./install_cron.sh
```

3. **Verify cron installation**:
```bash
crontab -l | grep monitor_check
```

4. **Check logs**:
```bash
tail -f /tmp/github_monitor_cron.log
```

## Deployment Option 2: Continuous Loop (Docker/Container)

**Best for**: Docker containers, systemd services, cloud platforms

1. **Run the monitoring loop**:
```bash
python3 run_monitor_loop.py
```

This runs continuously with a configurable interval (default 20 minutes).

2. **As a systemd service** (example):
```ini
[Unit]
Description=GitHub Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/github-monitor
Environment="GITHUB_TOKEN=ghp_your_token"
Environment="TELEGRAM_BOT_TOKEN=your_bot_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
ExecStart=/usr/bin/python3 run_monitor_loop.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Save as `/etc/systemd/system/github-monitor.service`, then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable github-monitor
sudo systemctl start github-monitor
sudo systemctl status github-monitor
```

## Deployment Option 3: Docker Container

**Best for**: Isolated deployment, multiple instances, cloud platforms

1. **Create Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY *.py /app/
COPY config.json.example /app/config.json

ENV GITHUB_TOKEN=""
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""

CMD ["python3", "run_monitor_loop.py"]
```

2. **Build and run**:
```bash
docker build -t github-monitor .
docker run -d \
  --name github-monitor \
  -e GITHUB_TOKEN="ghp_your_token" \
  -e TELEGRAM_BOT_TOKEN="your_bot_token" \
  -e TELEGRAM_CHAT_ID="your_chat_id" \
  -v $(pwd)/github_monitor.db:/app/github_monitor.db \
  github-monitor
```

3. **View logs**:
```bash
docker logs -f github-monitor
```

## Deployment Option 4: Cloud Platforms

### Railway / Render / Fly.io

1. **Create `Procfile`** (if needed):
```
worker: python3 run_monitor_loop.py
```

2. **Set environment variables** in platform dashboard:
- `GITHUB_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

3. **Deploy**:
```bash
git push <platform> master
```

### AWS Lambda (Scheduled)

Not ideal for continuous monitoring, but possible for one-shot checks:

1. Package dependencies with your code
2. Create Lambda function with Python 3.12 runtime
3. Set environment variables
4. Configure CloudWatch Events trigger (e.g., every 20 minutes)
5. Use `monitor_check.py` as the handler

## Configuration

### Required Settings

- `GITHUB_TOKEN`: GitHub personal access token with `repo` scope
- At least one of:
  - `watched_repos` in config.json
  - `auto_watch_user_repos: true` in config.json

### Optional Settings

**Telegram Notifications**:
- `TELEGRAM_BOT_TOKEN`: From @BotFather
- `TELEGRAM_CHAT_ID`: Your chat ID from @userinfobot

**Token Expiry Tracking**:
- `GITHUB_TOKEN_EXPIRES_AT`: ISO 8601 timestamp (e.g., "2026-03-15T00:00:00Z")

**Monitoring Interval**:
- `check_interval_minutes` in config.json (default: 20)

## Monitoring & Maintenance

### Check Status

```bash
# View database stats
sqlite3 github_monitor.db "SELECT COUNT(*) FROM repositories;"
sqlite3 github_monitor.db "SELECT COUNT(*) FROM issues;"
sqlite3 github_monitor.db "SELECT COUNT(*) FROM pull_requests;"

# View recent notifications
sqlite3 github_monitor.db "SELECT * FROM notifications ORDER BY created_at DESC LIMIT 10;"
```

### Backup Database

```bash
# Create backup
cp github_monitor.db github_monitor.db.backup

# Or use SQLite's backup command
sqlite3 github_monitor.db ".backup github_monitor.db.backup"
```

### Reset Database

```bash
# WARNING: This deletes all tracking data
rm github_monitor.db
python3 monitor_check.py  # Will recreate on next run
```

### Token Rotation

When rotating your GitHub token:

1. Generate new token at https://github.com/settings/tokens
2. Update environment variable or config
3. Set new `GITHUB_TOKEN_EXPIRES_AT` if applicable
4. Restart service

## Troubleshooting

### No notifications received

1. Check Telegram credentials:
```bash
python3 test_telegram.py
```

2. Check notification queue:
```bash
sqlite3 github_monitor.db "SELECT * FROM notifications WHERE sent = 0;"
```

3. Verify bot can message you:
   - Message your bot first (bots can't initiate conversations)
   - Check chat ID is correct

### GitHub API rate limits

- Authenticated requests: 5,000/hour
- Check remaining: Monitor output mentions rate limit status
- Solution: Reduce `check_interval_minutes` or watch fewer repos

### Database locked errors

- If running multiple instances, they'll compete for the database
- Solution: Use one instance or implement connection pooling

### Token expired

Monitor warns at 30 days, 7 days, and on expiry. Rotate before expiry.

## Security Best Practices

1. **Never commit tokens** - Use environment variables
2. **Restrict token scope** - Only `repo` scope needed
3. **Rotate tokens periodically** - Set expiry dates
4. **Secure database** - Contains repository metadata
5. **Protect Telegram credentials** - Bot token gives full bot access

## Performance Tuning

### For many repositories (50+)

- Increase `check_interval_minutes` to 30-60
- Consider watching only specific repos instead of `auto_watch_user_repos`
- Monitor API rate limits

### For low-resource environments

- Run `monitor_check.py` via cron instead of continuous loop
- Disable Telegram notifications if not needed
- Vacuum database periodically: `sqlite3 github_monitor.db "VACUUM;"`

## Support

- See `USAGE.md` for feature documentation
- See `README.md` for architecture overview
- Check test files for usage examples
