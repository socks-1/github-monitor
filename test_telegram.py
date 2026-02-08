#!/usr/bin/env python3
"""Test Telegram notification functionality."""

import os
from database import MonitorDB
from telegram_notifier import TelegramNotifier, send_pending_notifications


def main():
    """Test sending a notification via Telegram."""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        return 1

    print("Testing Telegram notification...")
    print(f"Bot Token: {bot_token[:20]}...")
    print(f"Chat ID: {chat_id}")

    # Initialize
    db = MonitorDB()
    notifier = TelegramNotifier(bot_token, chat_id)

    # Add a test notification to the database
    db.add_notification(
        'new_issue',
        'socks/test-repo',
        42,
        'Test notification from GitHub monitor'
    )

    # Send all pending notifications
    summary = send_pending_notifications(db, notifier)

    print(f"\nResults:")
    print(f"  Sent: {summary['sent']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Total: {summary['total']}")

    db.close()

    if summary['sent'] > 0:
        print("\n✅ Telegram notification test PASSED")
        return 0
    else:
        print("\n❌ Telegram notification test FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
