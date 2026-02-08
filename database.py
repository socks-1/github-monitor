#!/usr/bin/env python3
"""
Database layer for GitHub monitor.
Tracks repositories, issues, and PRs over time to detect changes.
"""

import sqlite3
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, List, Dict, Any


class MonitorDB:
    """SQLite database for tracking GitHub activity."""

    def __init__(self, db_path: str = "github_monitor.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize database connection and create tables if needed."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Create tables
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY,
                full_name TEXT UNIQUE NOT NULL,
                owner TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                last_push_at TEXT,
                first_seen_at TEXT NOT NULL,
                last_checked_at TEXT NOT NULL,
                is_watched INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY,
                repo_id INTEGER NOT NULL,
                issue_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                author TEXT,
                labels TEXT,
                first_seen_at TEXT NOT NULL,
                last_checked_at TEXT NOT NULL,
                FOREIGN KEY (repo_id) REFERENCES repositories (id),
                UNIQUE(repo_id, issue_number)
            );

            CREATE TABLE IF NOT EXISTS pull_requests (
                id INTEGER PRIMARY KEY,
                repo_id INTEGER NOT NULL,
                pr_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                author TEXT,
                labels TEXT,
                first_seen_at TEXT NOT NULL,
                last_checked_at TEXT NOT NULL,
                FOREIGN KEY (repo_id) REFERENCES repositories (id),
                UNIQUE(repo_id, pr_number)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                repo_full_name TEXT NOT NULL,
                item_number INTEGER,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sent_at TEXT,
                send_error TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_repos_watched ON repositories(is_watched);
            CREATE INDEX IF NOT EXISTS idx_issues_repo ON issues(repo_id);
            CREATE INDEX IF NOT EXISTS idx_prs_repo ON pull_requests(repo_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_sent ON notifications(sent_at);
        """)
        self.conn.commit()

    def upsert_repository(self, repo_data: Dict[str, Any]) -> int:
        """Insert or update a repository. Returns repo database ID."""
        now = datetime.now(UTC).isoformat()

        self.conn.execute("""
            INSERT INTO repositories (
                id, full_name, owner, name, description, last_push_at,
                first_seen_at, last_checked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(full_name) DO UPDATE SET
                description = excluded.description,
                last_push_at = excluded.last_push_at,
                last_checked_at = excluded.last_checked_at
        """, (
            repo_data.get('id'),
            repo_data['full_name'],
            repo_data['owner']['login'],
            repo_data['name'],
            repo_data.get('description'),
            repo_data.get('pushed_at'),
            now,
            now
        ))

        self.conn.commit()

        # Get the repo ID
        cursor = self.conn.execute(
            "SELECT id FROM repositories WHERE full_name = ?",
            (repo_data['full_name'],)
        )
        return cursor.fetchone()[0]

    def upsert_issue(self, repo_id: int, issue_data: Dict[str, Any]) -> tuple[bool, bool]:
        """
        Insert or update an issue.
        Returns (is_new, was_updated) tuple.
        """
        now = datetime.now(UTC).isoformat()
        labels = json.dumps([label['name'] for label in issue_data.get('labels', [])])

        # Check if issue exists and if it was updated
        existing = self.conn.execute("""
            SELECT updated_at FROM issues
            WHERE repo_id = ? AND issue_number = ?
        """, (repo_id, issue_data['number'])).fetchone()

        is_new = existing is None
        was_updated = False

        if existing:
            old_updated = existing[0]
            new_updated = issue_data['updated_at']
            was_updated = new_updated > old_updated

        self.conn.execute("""
            INSERT INTO issues (
                repo_id, issue_number, title, state, created_at, updated_at,
                author, labels, first_seen_at, last_checked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_id, issue_number) DO UPDATE SET
                title = excluded.title,
                state = excluded.state,
                updated_at = excluded.updated_at,
                labels = excluded.labels,
                last_checked_at = excluded.last_checked_at
        """, (
            repo_id,
            issue_data['number'],
            issue_data['title'],
            issue_data['state'],
            issue_data['created_at'],
            issue_data['updated_at'],
            issue_data['user']['login'],
            labels,
            now,
            now
        ))

        self.conn.commit()
        return (is_new, was_updated)

    def upsert_pull_request(self, repo_id: int, pr_data: Dict[str, Any]) -> tuple[bool, bool]:
        """
        Insert or update a pull request.
        Returns (is_new, was_updated) tuple.
        """
        now = datetime.now(UTC).isoformat()
        labels = json.dumps([label['name'] for label in pr_data.get('labels', [])])

        # Check if PR exists and if it was updated
        existing = self.conn.execute("""
            SELECT updated_at FROM pull_requests
            WHERE repo_id = ? AND pr_number = ?
        """, (repo_id, pr_data['number'])).fetchone()

        is_new = existing is None
        was_updated = False

        if existing:
            old_updated = existing[0]
            new_updated = pr_data['updated_at']
            was_updated = new_updated > old_updated

        self.conn.execute("""
            INSERT INTO pull_requests (
                repo_id, pr_number, title, state, created_at, updated_at,
                author, labels, first_seen_at, last_checked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_id, pr_number) DO UPDATE SET
                title = excluded.title,
                state = excluded.state,
                updated_at = excluded.updated_at,
                labels = excluded.labels,
                last_checked_at = excluded.last_checked_at
        """, (
            repo_id,
            pr_data['number'],
            pr_data['title'],
            pr_data['state'],
            pr_data['created_at'],
            pr_data['updated_at'],
            pr_data['user']['login'],
            labels,
            now,
            now
        ))

        self.conn.commit()
        return (is_new, was_updated)

    def add_notification(self, notif_type: str, repo_name: str, item_number: Optional[int], title: str):
        """Queue a notification to be sent."""
        now = datetime.now(UTC).isoformat()
        self.conn.execute("""
            INSERT INTO notifications (
                notification_type, repo_full_name, item_number, title, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (notif_type, repo_name, item_number, title, now))
        self.conn.commit()

    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get all notifications that haven't been sent yet."""
        cursor = self.conn.execute("""
            SELECT id, notification_type, repo_full_name, item_number, title, created_at
            FROM notifications
            WHERE sent_at IS NULL
            ORDER BY created_at ASC
        """)

        return [dict(row) for row in cursor.fetchall()]

    def mark_notification_sent(self, notif_id: int, error: Optional[str] = None):
        """Mark a notification as sent (or failed)."""
        now = datetime.now(UTC).isoformat()
        self.conn.execute("""
            UPDATE notifications
            SET sent_at = ?, send_error = ?
            WHERE id = ?
        """, (now, error, notif_id))
        self.conn.commit()

    def get_watched_repos(self) -> List[str]:
        """Get list of watched repository full names."""
        cursor = self.conn.execute("""
            SELECT full_name FROM repositories
            WHERE is_watched = 1
            ORDER BY last_push_at DESC
        """)
        return [row[0] for row in cursor.fetchall()]

    def set_repo_watched(self, full_name: str, watched: bool):
        """Mark a repository as watched or unwatched."""
        self.conn.execute("""
            UPDATE repositories
            SET is_watched = ?
            WHERE full_name = ?
        """, (1 if watched else 0, full_name))
        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    # Test the database
    db = MonitorDB("test.db")
    print("✓ Database initialized successfully")

    # Test repo insertion
    test_repo = {
        'id': 12345,
        'full_name': 'test/repo',
        'owner': {'login': 'test'},
        'name': 'repo',
        'description': 'Test repo',
        'pushed_at': '2026-02-08T00:00:00Z'
    }
    repo_id = db.upsert_repository(test_repo)
    print(f"✓ Repository inserted with ID: {repo_id}")

    # Test issue insertion
    test_issue = {
        'number': 1,
        'title': 'Test issue',
        'state': 'open',
        'created_at': '2026-02-08T00:00:00Z',
        'updated_at': '2026-02-08T00:00:00Z',
        'user': {'login': 'testuser'},
        'labels': [{'name': 'bug'}]
    }
    is_new, was_updated = db.upsert_issue(repo_id, test_issue)
    print(f"✓ Issue inserted (new={is_new}, updated={was_updated})")

    # Test notification
    db.add_notification('new_issue', 'test/repo', 1, 'Test issue')
    pending = db.get_pending_notifications()
    print(f"✓ Notification queued ({len(pending)} pending)")

    db.close()
    Path("test.db").unlink()
    print("✓ All database tests passed")
