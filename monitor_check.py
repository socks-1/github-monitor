#!/usr/bin/env python3
"""
Main monitoring script that checks for changes and sends notifications.
Designed to be run periodically via cron or systemd timer.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from github_client import GitHubClient
from database import MonitorDB
from monitor_daemon import ChangeDetector, print_summary
from telegram_notifier import TelegramNotifier, send_pending_notifications


def check_token_expiry(config: dict):
    """
    Check if GitHub token is expiring soon and print warnings.

    Args:
        config: Configuration dict
    """
    expires_at_env = config['github'].get('token_expires_at_env')
    if not expires_at_env:
        return

    expires_at_str = os.environ.get(expires_at_env)
    if not expires_at_str:
        return

    try:
        # Parse ISO format datetime (e.g., "2026-03-15T00:00:00Z")
        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days_until_expiry = (expires_at - now).days

        if days_until_expiry < 0:
            print(f"\n⚠️  WARNING: GitHub token EXPIRED {abs(days_until_expiry)} days ago!")
            print(f"   Please generate a new token and update {config['github']['token_env']}")
        elif days_until_expiry <= 7:
            print(f"\n⚠️  WARNING: GitHub token expires in {days_until_expiry} days")
            print(f"   Consider generating a new token soon")
        elif days_until_expiry <= 30:
            print(f"\nℹ️  GitHub token expires in {days_until_expiry} days")
    except (ValueError, TypeError) as e:
        print(f"\n⚠️  Could not parse {expires_at_env}: {e}")


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from file."""
    if Path(config_path).exists():
        with open(config_path) as f:
            return json.load(f)

    # Return default config
    return {
        "github": {
            "token_env": "GITHUB_TOKEN",
            "token_expires_at_env": "GITHUB_TOKEN_EXPIRES_AT",
            "watched_repos": []
        },
        "telegram": {
            "enabled": True,
            "bot_token_env": "TELEGRAM_BOT_TOKEN",
            "chat_id_env": "TELEGRAM_CHAT_ID"
        },
        "monitoring": {
            "auto_watch_user_repos": True,
            "max_repos_to_watch": 20,
            "check_interval_minutes": 20
        }
    }


def main():
    """Main monitoring check."""
    # Load config
    config = load_config()

    # Check token expiry
    check_token_expiry(config)

    # Get GitHub token
    token = os.environ.get(config['github']['token_env'])
    if not token:
        print(f"Error: {config['github']['token_env']} environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Initialize
    db = MonitorDB()
    github = GitHubClient(token)
    detector = ChangeDetector(db, github)

    # Determine which repositories to watch
    watched_repos = db.get_watched_repos()

    # Priority: 1) Database, 2) Config file, 3) Auto-discover
    if not watched_repos and config['github']['watched_repos']:
        # Use explicit configured watchlist
        watched_repos = config['github']['watched_repos']
        print(f"Watching {len(watched_repos)} configured repositories")

        # Fetch and store repo metadata for configured repos
        for repo_name in watched_repos:
            try:
                owner, name = repo_name.split('/')
                repo_data = github.get_repo(owner, name)
                if repo_data:
                    db.upsert_repository(repo_data)
            except Exception as e:
                print(f"Warning: Could not fetch metadata for {repo_name}: {e}")

    elif not watched_repos and config['monitoring']['auto_watch_user_repos']:
        # Auto-discover user's repositories
        print("First run - discovering your repositories...")
        repos = github.get_user_repos()
        max_repos = config['monitoring']['max_repos_to_watch']
        watched_repos = [repo['full_name'] for repo in repos[:max_repos]]

        # Add them to database
        for repo in repos[:max_repos]:
            db.upsert_repository(repo)

        print(f"Now watching {len(watched_repos)} repositories")

    if not watched_repos:
        print("No repositories to watch. Configure watched_repos or enable auto_watch_user_repos.")
        sys.exit(0)

    # Check for changes
    print(f"\nChecking {len(watched_repos)} repositories for changes...")
    summary = detector.check_repositories(watched_repos)

    # Print summary
    print_summary(summary)

    # Send Telegram notifications if enabled
    if config['telegram']['enabled']:
        bot_token = os.environ.get(config['telegram']['bot_token_env'])
        chat_id = os.environ.get(config['telegram']['chat_id_env'])

        if bot_token and chat_id:
            notifier = TelegramNotifier(bot_token, chat_id)
            notif_summary = send_pending_notifications(db, notifier)
            print(f"\n📱 Telegram: {notif_summary['sent']} sent, {notif_summary['failed']} failed")
        else:
            print(f"\n⚠️  Telegram credentials not configured (skipping notifications)")

    db.close()
    print("\n✓ Monitoring check complete")


if __name__ == "__main__":
    main()
