#!/usr/bin/env python3
"""
Telegram notification handler for GitHub monitor.
Sends queued notifications via Telegram bot.
"""

import os
import sys
import json
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from database import MonitorDB


class TelegramNotifier:
    """Sends notifications via Telegram bot."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message via Telegram bot."""
        url = f"{self.base_url}/sendMessage"
        data = json.dumps({
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }).encode('utf-8')

        req = Request(url, data=data, headers={'Content-Type': 'application/json'})

        try:
            with urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('ok', False)
        except (HTTPError, URLError, Exception) as e:
            print(f"Telegram send error: {e}", file=sys.stderr)
            return False

    def format_notification(self, notif: dict) -> str:
        """Format a notification as HTML text."""
        notif_type = notif['notification_type']
        repo = notif['repo_full_name']
        title = notif['title']
        number = notif.get('item_number')

        emoji_map = {
            'new_issue': '🆕',
            'updated_issue': '📝',
            'new_pr': '🔀',
            'updated_pr': '📝'
        }

        type_name_map = {
            'new_issue': 'New Issue',
            'updated_issue': 'Issue Updated',
            'new_pr': 'New PR',
            'updated_pr': 'PR Updated'
        }

        emoji = emoji_map.get(notif_type, '📢')
        type_name = type_name_map.get(notif_type, notif_type)

        if number:
            url = f"https://github.com/{repo}/issues/{number}"
            if 'pr' in notif_type:
                url = f"https://github.com/{repo}/pull/{number}"

            return f"{emoji} <b>{type_name}</b>\n" \
                   f"<b>{repo}#{number}</b>\n" \
                   f"{title}\n" \
                   f"<a href=\"{url}\">View on GitHub</a>"
        else:
            return f"{emoji} <b>{type_name}</b>\n" \
                   f"<b>{repo}</b>\n" \
                   f"{title}"


def send_pending_notifications(db: MonitorDB, notifier: TelegramNotifier) -> dict:
    """Send all pending notifications and return summary."""
    pending = db.get_pending_notifications()

    summary = {
        'sent': 0,
        'failed': 0,
        'total': len(pending)
    }

    for notif in pending:
        message = notifier.format_notification(notif)
        success = notifier.send_message(message)

        if success:
            db.mark_notification_sent(notif['id'])
            summary['sent'] += 1
        else:
            db.mark_notification_sent(notif['id'], error="Failed to send")
            summary['failed'] += 1

    return summary


def main():
    """Send pending notifications."""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set", file=sys.stderr)
        sys.exit(1)

    db = MonitorDB()
    notifier = TelegramNotifier(bot_token, chat_id)

    summary = send_pending_notifications(db, notifier)

    print(f"Notifications: {summary['sent']} sent, {summary['failed']} failed, {summary['total']} total")

    db.close()


if __name__ == "__main__":
    main()
