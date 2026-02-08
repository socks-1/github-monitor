#!/usr/bin/env python3
"""
Integration test for GitHub Monitor.
Tests the full monitoring cycle without hitting real GitHub API.
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone


class MockGitHubClient:
    """Mock GitHub client for testing."""

    def __init__(self, token=None):
        self.token = token
        self._repo_call_counts = {}

    def get_user_repos(self, limit=30):
        """Return mock repository data."""
        return [
            {
                'id': 1001,
                'full_name': 'socks/project-alpha',
                'name': 'project-alpha',
                'owner': {'login': 'socks'},
                'description': 'First project',
                'pushed_at': datetime.now(timezone.utc).isoformat(),
                'stargazers_count': 5,
                'forks_count': 2,
                'open_issues_count': 3
            }
        ]

    def get_repo_issues(self, repo, state='open', limit=50):
        """Return mock issue data."""
        # Track per-repo calls
        if repo not in self._repo_call_counts:
            self._repo_call_counts[repo] = 0
        self._repo_call_counts[repo] += 1

        call_num = self._repo_call_counts[repo]

        if call_num == 1:
            # First call - return one issue
            return [{
                'id': 2001,
                'number': 1,
                'title': 'First issue',
                'state': 'open',
                'user': {'login': 'contributor1'},
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'html_url': f'https://github.com/{repo}/issues/1'
            }]
        else:
            # Second call - return two issues (one new)
            return [
                {
                    'id': 2001,
                    'number': 1,
                    'title': 'First issue',
                    'state': 'open',
                    'user': {'login': 'contributor1'},
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'html_url': f'https://github.com/{repo}/issues/1'
                },
                {
                    'id': 2002,
                    'number': 2,
                    'title': 'Second issue',
                    'state': 'open',
                    'user': {'login': 'contributor2'},
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'html_url': f'https://github.com/{repo}/issues/2'
                }
            ]

    def get_repo_prs(self, repo, state='open', limit=50):
        """Return mock PR data."""
        return []


def test_full_monitoring_cycle():
    """Test complete monitoring cycle."""
    print("\n" + "="*60)
    print("  Integration Test - Full Monitoring Cycle")
    print("="*60 + "\n")

    # Create temporary database
    temp_db = tempfile.mktemp(suffix='.db')

    try:
        from database import MonitorDB
        from monitor_daemon import ChangeDetector

        db = MonitorDB(temp_db)
        github = MockGitHubClient("test_token")
        detector = ChangeDetector(db, github)

        # First run - should detect all as new
        print("=== First Monitoring Run ===\n")
        print("Initializing with user repos...")
        repos = github.get_user_repos()
        for repo in repos:
            db.upsert_repository(repo)

        repo_names = [r['full_name'] for r in repos]
        print(f"Watching: {repo_names}")
        assert len(repo_names) == 1, "Should be watching 1 repo"

        print("\nChecking for changes...")
        summary = detector.check_repositories(repo_names)

        print(f"  New issues: {len(summary['new_issues'])}")
        print(f"  Updated issues: {len(summary['updated_issues'])}")
        print(f"  New PRs: {len(summary['new_prs'])}")
        print(f"  Errors: {len(summary['errors'])}")

        # Check notifications were queued
        pending = db.get_pending_notifications()
        print(f"  Queued notifications: {len(pending)}")

        assert len(summary['new_issues']) == 1, "Should have 1 new issue on first run"
        assert len(pending) == 1, "Should have 1 pending notification"

        # Mark notifications as sent
        for notif in pending:
            db.mark_notification_sent(notif['id'])

        # Second run - should detect one new issue
        print("\n=== Second Monitoring Run ===\n")
        print("Checking for changes...")
        summary = detector.check_repositories(repo_names)

        print(f"  New issues: {len(summary['new_issues'])}")
        print(f"  Updated issues: {len(summary['updated_issues'])}")
        print(f"  New PRs: {len(summary['new_prs'])}")
        print(f"  Errors: {len(summary['errors'])}")

        pending = db.get_pending_notifications()
        print(f"  Queued notifications: {len(pending)}")

        # Should detect 1 new issue and possibly 1 updated (due to timestamp matching)
        assert len(summary['new_issues']) == 1, "Should have 1 new issue on second run"
        # Could be 1 or 2 depending on whether existing issue looks updated
        assert len(pending) >= 1, "Should have at least 1 new pending notification"

        # Verify database state
        print("\n=== Database State ===\n")
        cursor = db.conn.execute("SELECT COUNT(*) FROM repositories")
        repo_count = cursor.fetchone()[0]
        print(f"  Repositories tracked: {repo_count}")
        assert repo_count == 1

        cursor = db.conn.execute("SELECT COUNT(*) FROM issues")
        issue_count = cursor.fetchone()[0]
        print(f"  Issues tracked: {issue_count}")
        assert issue_count == 2

        cursor = db.conn.execute("SELECT COUNT(*) FROM notifications WHERE sent_at IS NOT NULL")
        sent_count = cursor.fetchone()[0]
        print(f"  Notifications sent: {sent_count}")
        assert sent_count == 1

        cursor = db.conn.execute("SELECT COUNT(*) FROM notifications WHERE sent_at IS NULL")
        pending_count = cursor.fetchone()[0]
        print(f"  Notifications pending: {pending_count}")
        assert pending_count >= 1, "Should have at least 1 pending notification"

        db.close()

        print("\n✅ Integration test passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if Path(temp_db).exists():
            Path(temp_db).unlink()


if __name__ == "__main__":
    success = test_full_monitoring_cycle()
    sys.exit(0 if success else 1)
