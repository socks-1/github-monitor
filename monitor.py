#!/usr/bin/env python3
"""
GitHub Monitor - Aggregates and displays repository activity.

Monitors repos for:
- Recent commits/pushes
- Open issues and PRs
- Repository activity
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any
from github_client import GitHubClient


def format_timestamp(timestamp: str) -> str:
    """Convert ISO timestamp to relative time."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
    except:
        return timestamp


def display_repo_summary(client: GitHubClient, limit: int = 10):
    """Display summary of user's repositories."""
    print("=" * 80)
    print("GITHUB ACTIVITY MONITOR")
    print("=" * 80)

    # Get user info
    user = client.get_user_info()
    print(f"\n👤 User: {user.get('login')} ({user.get('name', 'N/A')})")
    print(f"📦 Public repos: {user.get('public_repos', 0)}")
    print(f"👥 Followers: {user.get('followers', 0)} | Following: {user.get('following', 0)}")

    # Get repositories
    print(f"\n📚 Recent Repositories (sorted by last push):")
    print("-" * 80)
    repos = client.get_user_repos(limit=limit)

    for i, repo in enumerate(repos, 1):
        name = repo['name']
        desc = repo.get('description', 'No description')[:60]
        stars = repo['stargazers_count']
        forks = repo['forks_count']
        pushed_at = format_timestamp(repo['pushed_at'])
        is_private = "🔒" if repo.get('private', False) else "📂"

        print(f"{i:2}. {is_private} {name}")
        print(f"    {desc}")
        print(f"    ⭐ {stars} | 🍴 {forks} | 📝 Last push: {pushed_at}")
        print()


def display_repo_detail(client: GitHubClient, repo_name: str):
    """Display detailed info about a specific repository."""
    print("=" * 80)
    print(f"REPOSITORY: {repo_name}")
    print("=" * 80)

    # Get issues
    print("\n🐛 Open Issues:")
    print("-" * 80)
    issues = client.get_repo_issues(repo_name, state="open", limit=10)

    # Filter out PRs (GitHub API returns PRs as issues too)
    actual_issues = [i for i in issues if 'pull_request' not in i]

    if not actual_issues:
        print("  No open issues")
    else:
        for issue in actual_issues[:5]:
            num = issue['number']
            title = issue['title'][:60]
            created = format_timestamp(issue['created_at'])
            labels = ', '.join([l['name'] for l in issue.get('labels', [])])

            print(f"  #{num}: {title}")
            if labels:
                print(f"      🏷️  {labels}")
            print(f"      📅 Created {created} by {issue['user']['login']}")
            print()

    # Get PRs
    print("\n🔀 Open Pull Requests:")
    print("-" * 80)
    prs = client.get_repo_prs(repo_name, state="open", limit=10)

    if not prs:
        print("  No open PRs")
    else:
        for pr in prs[:5]:
            num = pr['number']
            title = pr['title'][:60]
            created = format_timestamp(pr['created_at'])
            author = pr['user']['login']

            print(f"  #{num}: {title}")
            print(f"      📅 Created {created} by {author}")
            print()


def display_activity_dashboard(client: GitHubClient, repo_limit: int = 5):
    """Display a dashboard of activity across repositories."""
    print("=" * 80)
    print("ACTIVITY DASHBOARD")
    print("=" * 80)

    repos = client.get_user_repos(limit=repo_limit)

    total_issues = 0
    total_prs = 0
    recent_activity = []

    for repo in repos:
        repo_name = repo['full_name']

        # Get open issues and PRs
        issues = client.get_repo_issues(repo_name, state="open", limit=50)
        prs = client.get_repo_prs(repo_name, state="open", limit=50)

        actual_issues = [i for i in issues if 'pull_request' not in i]

        total_issues += len(actual_issues)
        total_prs += len(prs)

        # Track repos with activity
        if actual_issues or prs:
            recent_activity.append({
                'name': repo_name,
                'issues': len(actual_issues),
                'prs': len(prs),
                'pushed': repo['pushed_at']
            })

    print(f"\n📊 Summary across {len(repos)} repositories:")
    print(f"  🐛 Total open issues: {total_issues}")
    print(f"  🔀 Total open PRs: {total_prs}")

    if recent_activity:
        print(f"\n📌 Repositories with activity:")
        print("-" * 80)
        for item in sorted(recent_activity, key=lambda x: x['pushed'], reverse=True):
            pushed = format_timestamp(item['pushed'])
            print(f"  {item['name']}")
            print(f"    🐛 {item['issues']} issues | 🔀 {item['prs']} PRs | 📝 {pushed}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "summary"

    try:
        client = GitHubClient()

        if mode == "summary":
            display_repo_summary(client)
        elif mode == "dashboard":
            display_activity_dashboard(client)
        elif mode.startswith("repo:"):
            repo_name = mode.split(":", 1)[1]
            display_repo_detail(client, repo_name)
        else:
            print("Usage: python monitor.py [summary|dashboard|repo:owner/name]")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
