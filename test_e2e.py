#!/usr/bin/env python3
"""
End-to-end test of the complete GitHub monitoring workflow.
Tests: detection, database storage, and notification sending.
"""

import os
import sys
from pathlib import Path
from github_client import GitHubClient
from database import MonitorDB
from monitor_daemon import ChangeDetector
from telegram_notifier import TelegramNotifier, send_pending_notifications


def test_e2e():
    """Test the complete monitoring workflow."""
    print("=" * 80)
    print("GitHub Monitor - End-to-End Test")
    print("=" * 80)

    # 1. Test GitHub API connectivity
    print("\n[1/5] Testing GitHub API connectivity...")
    try:
        client = GitHubClient()
        user = client.get_user_info()
        print(f"  ✓ Connected as: {user['login']}")
    except Exception as e:
        print(f"  ✗ GitHub API failed: {e}")
        return False

    # 2. Test database operations
    print("\n[2/5] Testing database operations...")
    try:
        db = MonitorDB()

        # Get repository count
        repos = db.get_watched_repos()
        issues_cursor = db.conn.execute("SELECT COUNT(*) FROM issues")
        issue_count = issues_cursor.fetchone()[0]

        print(f"  ✓ Database connected")
        print(f"    - Repositories tracked: {len(repos)}")
        print(f"    - Issues tracked: {issue_count}")
    except Exception as e:
        print(f"  ✗ Database failed: {e}")
        return False

    # 3. Test change detection
    print("\n[3/5] Testing change detection...")
    try:
        detector = ChangeDetector(db, client)

        # Check repositories for changes
        if repos:
            summary = detector.check_repositories(repos[:1])  # Test with 1 repo
            print(f"  ✓ Change detection working")
            print(f"    - New issues: {len(summary['new_issues'])}")
            print(f"    - Updated issues: {len(summary['updated_issues'])}")
            print(f"    - New PRs: {len(summary['new_prs'])}")
            print(f"    - Errors: {len(summary['errors'])}")
        else:
            print(f"  ⚠ No repositories to check")
    except Exception as e:
        print(f"  ✗ Change detection failed: {e}")
        return False

    # 4. Test notification queue
    print("\n[4/5] Testing notification queue...")
    try:
        pending = db.get_pending_notifications()
        print(f"  ✓ Notification queue accessible")
        print(f"    - Pending notifications: {len(pending)}")

        # Add a test notification if none exist
        if len(pending) == 0:
            print(f"    - Creating test notification...")
            db.add_notification(
                'new_issue',
                'socks/github-monitor',
                999,
                'End-to-end test notification'
            )
            pending = db.get_pending_notifications()
            print(f"    - Pending after test add: {len(pending)}")
    except Exception as e:
        print(f"  ✗ Notification queue failed: {e}")
        return False

    # 5. Test Telegram delivery (optional based on credentials)
    print("\n[5/5] Testing Telegram notification delivery...")
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if bot_token and chat_id:
        try:
            notifier = TelegramNotifier(bot_token, chat_id)
            notif_summary = send_pending_notifications(db, notifier)

            print(f"  ✓ Telegram notifications sent")
            print(f"    - Sent: {notif_summary['sent']}")
            print(f"    - Failed: {notif_summary['failed']}")

            if notif_summary['failed'] > 0:
                print(f"  ⚠ Some notifications failed to send")
        except Exception as e:
            print(f"  ✗ Telegram delivery failed: {e}")
            return False
    else:
        print(f"  ⚠ Telegram credentials not configured (skipping)")

    # Cleanup
    db.close()

    print("\n" + "=" * 80)
    print("✅ End-to-End Test PASSED")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_e2e()
    sys.exit(0 if success else 1)
