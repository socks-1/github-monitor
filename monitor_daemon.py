#!/usr/bin/env python3
"""
GitHub monitor daemon that tracks changes and triggers notifications.
Can be run as a one-shot check or scheduled via cron.
"""

import os
import sys
from typing import List, Dict, Any
from github_client import GitHubClient
from database import MonitorDB


class ChangeDetector:
    """Detects new and updated issues/PRs."""

    def __init__(self, db: MonitorDB, github: GitHubClient):
        self.db = db
        self.github = github

    def check_repositories(self, repo_names: List[str]) -> Dict[str, Any]:
        """
        Check repositories for changes.
        Returns summary of new/updated items.
        """
        summary = {
            'new_issues': [],
            'updated_issues': [],
            'new_prs': [],
            'updated_prs': [],
            'errors': []
        }

        for repo_name in repo_names:
            try:
                self._check_repository(repo_name, summary)
            except Exception as e:
                summary['errors'].append(f"{repo_name}: {str(e)}")

        return summary

    def _check_repository(self, repo_name: str, summary: Dict[str, Any]):
        """Check a single repository for changes."""
        # Note: We need to get repo data from the database or user_repos call
        # For now, just get the repo_id from database
        cursor = self.db.conn.execute(
            "SELECT id FROM repositories WHERE full_name = ?",
            (repo_name,)
        )
        row = cursor.fetchone()
        if not row:
            summary['errors'].append(f"{repo_name}: Not found in database")
            return

        repo_id = row['id']

        # Check issues
        issues = self.github.get_repo_issues(repo_name)
        for issue in issues:
            is_new, was_updated = self.db.upsert_issue(repo_id, issue)

            if is_new:
                summary['new_issues'].append({
                    'repo': repo_name,
                    'number': issue['number'],
                    'title': issue['title'],
                    'author': issue['user']['login']
                })
                self.db.add_notification(
                    'new_issue',
                    repo_name,
                    issue['number'],
                    issue['title']
                )
            elif was_updated:
                summary['updated_issues'].append({
                    'repo': repo_name,
                    'number': issue['number'],
                    'title': issue['title']
                })
                self.db.add_notification(
                    'updated_issue',
                    repo_name,
                    issue['number'],
                    issue['title']
                )

        # Check pull requests
        prs = self.github.get_repo_prs(repo_name)
        for pr in prs:
            is_new, was_updated = self.db.upsert_pull_request(repo_id, pr)

            if is_new:
                summary['new_prs'].append({
                    'repo': repo_name,
                    'number': pr['number'],
                    'title': pr['title'],
                    'author': pr['user']['login']
                })
                self.db.add_notification(
                    'new_pr',
                    repo_name,
                    pr['number'],
                    pr['title']
                )
            elif was_updated:
                summary['updated_prs'].append({
                    'repo': repo_name,
                    'number': pr['number'],
                    'title': pr['title']
                })
                self.db.add_notification(
                    'updated_pr',
                    repo_name,
                    pr['number'],
                    pr['title']
                )


def print_summary(summary: Dict[str, Any]):
    """Print a human-readable summary of changes."""
    total_changes = (
        len(summary['new_issues']) +
        len(summary['updated_issues']) +
        len(summary['new_prs']) +
        len(summary['updated_prs'])
    )

    if total_changes == 0:
        print("✓ No changes detected")
    else:
        print(f"\n{'='*60}")
        print(f"  GitHub Activity Summary - {total_changes} changes detected")
        print(f"{'='*60}\n")

    if summary['new_issues']:
        print(f"🆕 New Issues ({len(summary['new_issues'])})")
        for item in summary['new_issues']:
            print(f"  • {item['repo']}#{item['number']}: {item['title']}")
            print(f"    by @{item['author']}")
        print()

    if summary['updated_issues']:
        print(f"📝 Updated Issues ({len(summary['updated_issues'])})")
        for item in summary['updated_issues']:
            print(f"  • {item['repo']}#{item['number']}: {item['title']}")
        print()

    if summary['new_prs']:
        print(f"🆕 New Pull Requests ({len(summary['new_prs'])})")
        for item in summary['new_prs']:
            print(f"  • {item['repo']}#{item['number']}: {item['title']}")
            print(f"    by @{item['author']}")
        print()

    if summary['updated_prs']:
        print(f"📝 Updated Pull Requests ({len(summary['updated_prs'])})")
        for item in summary['updated_prs']:
            print(f"  • {item['repo']}#{item['number']}: {item['title']}")
        print()

    if summary['errors']:
        print(f"❌ Errors ({len(summary['errors'])})")
        for error in summary['errors']:
            print(f"  • {error}")
        print()


def main():
    """Main entry point for the monitoring daemon."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Initialize
    db = MonitorDB()
    github = GitHubClient(token)
    detector = ChangeDetector(db, github)

    # Get watched repositories
    watched_repos = db.get_watched_repos()

    if not watched_repos:
        # First run - get user's repositories and watch them all
        print("First run - discovering your repositories...")
        repos = github.get_user_repos()
        watched_repos = [repo['full_name'] for repo in repos[:20]]  # Start with first 20

        # Add them to database
        for repo in repos[:20]:
            db.upsert_repository(repo)

        print(f"Now watching {len(watched_repos)} repositories")

    # Check for changes
    print(f"Checking {len(watched_repos)} repositories for changes...")
    summary = detector.check_repositories(watched_repos)

    # Print summary
    print_summary(summary)

    db.close()


if __name__ == "__main__":
    main()
