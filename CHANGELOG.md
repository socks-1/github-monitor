# Changelog

All notable changes to GitHub Monitor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-08

### Added
- Initial release of GitHub Monitor
- GitHub API client using pure Python stdlib (no external dependencies)
- SQLite database for persistent change tracking
- Repository, issue, and pull request monitoring
- Change detection for new and updated items
- Telegram notification system with HTML formatting
- Three deployment modes:
  - One-shot check (monitor_check.py) for cron jobs
  - Continuous loop (run_monitor_loop.py) for containers
  - Cron installation script (install_cron.sh)
- Configuration system (config.json) with:
  - Watched repository list
  - Auto-watch user repositories option
  - Telegram integration settings
  - Configurable check intervals
- GitHub token expiry tracking and warnings
- Comprehensive test suite:
  - Unit tests (test_github_monitor.py)
  - Integration tests (test_integration.py)
  - End-to-end tests (test_e2e.py)
  - Telegram notification tests (test_telegram.py)
- Docker support:
  - Dockerfile for containerized deployment
  - docker-compose.yml for easy setup
- Complete documentation:
  - README.md with feature overview
  - USAGE.md with detailed usage examples
  - DEPLOY.md with deployment guides for multiple platforms
  - CHANGELOG.md (this file)
- MIT License

### Features
- **Zero external dependencies** - Pure Python 3.12+ stdlib
- **Smart change detection** - Only notifies on actual changes
- **Flexible deployment** - Cron, Docker, systemd, cloud platforms
- **Telegram integration** - Rich HTML-formatted notifications
- **Token expiry tracking** - Proactive warnings before token expiration
- **Relative timestamps** - Human-readable time formats ("2h ago")
- **Database persistence** - SQLite for reliable state tracking
- **Auto-discovery** - Option to automatically watch all user repositories

### Technical Highlights
- Lightweight architecture with minimal resource usage
- Clean separation of concerns (client, database, notifier, daemon)
- Idempotent operations for safe re-runs
- Comprehensive error handling
- Production-tested with real GitHub API

### Deployment Support
- Linux (cron)
- Docker/Docker Compose
- systemd services
- Cloud platforms (Railway, Render, Fly.io)
- AWS Lambda (scheduled)

## [Unreleased]

### Planned
- Web dashboard for monitoring status
- Support for GitHub Actions workflow monitoring
- Enhanced filtering options
- Multi-user support
- Metrics and statistics dashboard
