#!/usr/bin/env python3
"""
Simple GitHub API client using direct HTTP requests.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Any


class GitHubClient:
    """GitHub API client using urllib for HTTP requests."""

    def __init__(self, token: str | None = None):
        """
        Initialize the client with a GitHub token.

        Args:
            token: GitHub personal access token (defaults to GITHUB_TOKEN env var)
        """
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        if not self.token:
            raise RuntimeError("GitHub token not provided and GITHUB_TOKEN env var not set")

        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Socks-GitHub-Monitor/1.0"
        }

    def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """
        Make a GET request to the GitHub API.

        Args:
            endpoint: API endpoint (e.g., "/user")
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}{endpoint}"

        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query_string}"

        req = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(f"GitHub API error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")

    def get_user_repos(self, limit: int = 30) -> list[dict[str, Any]]:
        """
        Get repositories for the authenticated user.

        Args:
            limit: Maximum number of repos to fetch

        Returns:
            List of repository data dicts
        """
        return self._request("/user/repos", {"per_page": limit, "sort": "pushed"})

    def get_repo(self, owner: str, name: str) -> dict[str, Any]:
        """
        Get metadata for a specific repository.

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            Repository data dict
        """
        return self._request(f"/repos/{owner}/{name}")

    def get_repo_issues(self, repo: str, state: str = "open", limit: int = 50) -> list[dict[str, Any]]:
        """
        Get issues for a repository.

        Args:
            repo: Repository name in format "owner/repo"
            state: Issue state (open, closed, all)
            limit: Maximum number of issues

        Returns:
            List of issue data dicts
        """
        return self._request(f"/repos/{repo}/issues", {
            "state": state,
            "per_page": limit
        })

    def get_repo_prs(self, repo: str, state: str = "open", limit: int = 50) -> list[dict[str, Any]]:
        """
        Get pull requests for a repository.

        Args:
            repo: Repository name in format "owner/repo"
            state: PR state (open, closed, all)
            limit: Maximum number of PRs

        Returns:
            List of PR data dicts
        """
        return self._request(f"/repos/{repo}/pulls", {
            "state": state,
            "per_page": limit
        })

    def get_user_info(self) -> dict[str, Any]:
        """
        Get authenticated user information.

        Returns:
            User data dict
        """
        return self._request("/user")


if __name__ == "__main__":
    # Quick test
    client = GitHubClient()

    print("=== User Info ===")
    user = client.get_user_info()
    print(f"Username: {user.get('login')}")
    print(f"Name: {user.get('name')}")
    print(f"Public repos: {user.get('public_repos')}")

    print("\n=== Repositories ===")
    repos = client.get_user_repos(limit=5)
    for repo in repos:
        print(f"- {repo['name']}: {repo.get('description', 'No description')}")
        print(f"  ⭐ {repo['stargazers_count']} | 🍴 {repo['forks_count']} | {repo['html_url']}")
