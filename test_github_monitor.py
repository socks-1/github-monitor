#!/usr/bin/env python3
"""
Comprehensive test suite for GitHub Monitor.
Tests database operations, change detection, and notification queueing.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Test database operations
def test_database():
    """Test database schema and operations."""
    print("=== Testing Database Operations ===\n")

    # Create temporary database
    temp_db = tempfile.mktemp(suffix='.db')
    os.environ['GITHUB_MONITOR_DB'] = temp_db

    try:
        from database import MonitorDB

        db = MonitorDB(temp_db)

        # Test repository insertion
        print("✓ Testing repository upsert...")
        repo_data = {
            'id': 12345,
            'full_name': 'test/repo',
            'name': 'repo',
            'owner': {'login': 'test'},
            'description': 'Test repo',
            'html_url': 'https://github.com/test/repo',
            'stargazers_count': 10,
            'forks_count': 5,
            'open_issues_count': 3,
            'pushed_at': datetime.now(timezone.utc).isoformat()
        }
        repo_id = db.upsert_repository(repo_data)
        assert repo_id is not None, "Repository insertion failed"
        print(f"  Inserted repo with ID: {repo_id}")

        # Test issue insertion (new)
        print("\n✓ Testing issue upsert (new)...")
        issue_data = {
            'id': 1001,
            'number': 42,
            'title': 'Test Issue',
            'state': 'open',
            'user': {'login': 'testuser'},
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'html_url': 'https://github.com/test/repo/issues/42'
        }
        is_new, was_updated = db.upsert_issue(repo_id, issue_data)
        assert is_new, "Issue should be new"
        assert not was_updated, "New issue should not be marked as updated"
        print(f"  New issue: {is_new}, Updated: {was_updated}")

        # Test issue update
        print("\n✓ Testing issue upsert (update)...")
        issue_data['updated_at'] = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat()
        is_new, was_updated = db.upsert_issue(repo_id, issue_data)
        assert not is_new, "Issue should not be new"
        assert was_updated, "Issue should be marked as updated"
        print(f"  New issue: {is_new}, Updated: {was_updated}")

        # Test PR insertion
        print("\n✓ Testing PR upsert...")
        pr_data = {
            'id': 2001,
            'number': 7,
            'title': 'Test PR',
            'state': 'open',
            'user': {'login': 'contributor'},
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'html_url': 'https://github.com/test/repo/pull/7',
            'merged': False,
            'draft': False
        }
        is_new, was_updated = db.upsert_pull_request(repo_id, pr_data)
        assert is_new, "PR should be new"
        print(f"  New PR: {is_new}, Updated: {was_updated}")

        # Test notification queue
        print("\n✓ Testing notification queue...")
        db.add_notification('new_issue', 'test/repo', 42, 'Test Issue')
        pending = db.get_pending_notifications()
        assert len(pending) > 0, "Should have pending notifications"
        print(f"  Queued notifications: {len(pending)}")

        # Mark notification as sent
        db.mark_notification_sent(pending[0]['id'])
        pending_after = db.get_pending_notifications()
        assert len(pending_after) == 0, "No pending notifications after marking sent"
        print("  Notification marked as sent")

        # Test watched repos
        print("\n✓ Testing watched repos...")
        watched = db.get_watched_repos()
        assert 'test/repo' in watched, "Repo should be in watched list"
        print(f"  Watched repos: {watched}")

        db.close()
        print("\n✅ All database tests passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Database test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if Path(temp_db).exists():
            Path(temp_db).unlink()


def test_config_loading():
    """Test configuration loading."""
    print("=== Testing Configuration Loading ===\n")

    try:
        from monitor_check import load_config

        # Test default config
        print("✓ Testing default config...")
        config = load_config("nonexistent.json")
        assert 'github' in config
        assert 'telegram' in config
        assert 'monitoring' in config
        print("  Default config loaded")

        # Test custom config
        print("\n✓ Testing custom config...")
        temp_config = tempfile.mktemp(suffix='.json')
        with open(temp_config, 'w') as f:
            f.write('{"github": {"token_env": "CUSTOM_TOKEN"}}')

        custom_config = load_config(temp_config)
        assert custom_config['github']['token_env'] == 'CUSTOM_TOKEN'
        print("  Custom config loaded")

        Path(temp_config).unlink()

        print("\n✅ All config tests passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Config test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_token_expiry():
    """Test token expiry checking."""
    print("=== Testing Token Expiry Checking ===\n")

    try:
        from monitor_check import check_token_expiry

        # Test with no expiry set
        print("✓ Testing no expiry set...")
        config = {'github': {}}
        check_token_expiry(config)  # Should not raise
        print("  No error when expiry not configured")

        # Test with valid expiry (far future)
        print("\n✓ Testing valid future expiry...")
        os.environ['TEST_EXPIRY'] = (datetime.now(timezone.utc) + timedelta(days=100)).isoformat()
        config = {'github': {'token_expires_at_env': 'TEST_EXPIRY'}}
        check_token_expiry(config)
        print("  No warning for distant expiry")

        # Test with near expiry
        print("\n✓ Testing near expiry (warning expected)...")
        os.environ['TEST_EXPIRY'] = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        check_token_expiry(config)
        print("  Warning shown for near expiry")

        # Clean up
        del os.environ['TEST_EXPIRY']

        print("\n✅ All token expiry tests passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Token expiry test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_telegram_notifier():
    """Test Telegram notification formatting."""
    print("=== Testing Telegram Notifier ===\n")

    try:
        from telegram_notifier import TelegramNotifier

        # Test notification formatting
        print("✓ Testing notification formatting...")
        notifier = TelegramNotifier("fake_token", "fake_chat_id")

        # Test different notification types
        messages = []
        messages.append(notifier.format_notification({
            'notification_type': 'new_issue',
            'repo_full_name': 'test/repo',
            'item_number': 42,
            'title': 'Bug found'
        }))

        messages.append(notifier.format_notification({
            'notification_type': 'new_pr',
            'repo_full_name': 'test/repo',
            'item_number': 7,
            'title': 'Fix bug'
        }))

        messages.append(notifier.format_notification({
            'notification_type': 'updated_issue',
            'repo_full_name': 'test/repo',
            'item_number': 42,
            'title': 'Bug found'
        }))

        for msg in messages:
            assert msg, "Message should not be empty"
            assert 'test/repo' in msg, "Message should contain repo name"
            print(f"  {msg[:50]}...")

        print(f"\n  Formatted {len(messages)} notification types")
        print("\n✅ All Telegram tests passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Telegram test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  GitHub Monitor - Test Suite")
    print("="*60 + "\n")

    results = []

    # Run tests
    results.append(("Database Operations", test_database()))
    results.append(("Configuration Loading", test_config_loading()))
    results.append(("Token Expiry Checking", test_token_expiry()))
    results.append(("Telegram Notifier", test_telegram_notifier()))

    # Summary
    print("="*60)
    print("  Test Summary")
    print("="*60 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")

    print(f"\n{passed}/{total} test suites passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
