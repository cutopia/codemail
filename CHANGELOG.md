# Changelog

All notable changes to Codemail will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project workspace isolation for task execution
- Comprehensive error reporting with diagnostic information

### Changed
- Enhanced command filtering to prevent natural language execution as bash commands

### Fixed
- File creation verification in agent loop
- Email whitelist extraction logic

## [1.0.0] - 2026-04-09

### Added
- Initial release of Codemail
- Email-based task submission via IMAP monitoring
- LLM-powered agentic task execution
- SMTP reporting for task completion status
- Email whitelist security feature (sender/recipient control)
- REST API for queue status monitoring
- Celery-based async task processing with Redis

### Features
- 📧 Email-driven interface for remote coding tasks
- 🔒 Built-in email whitelist for security
- 🔄 Agentic loop with iterative refinement
- 📊 Real-time task tracking and reporting
- ⚡ Async execution with Celery queue management

## Documentation Structure

This project uses a streamlined documentation approach:

| File | Purpose |
|------|---------|
| `README.md` | Main project overview and quick start guide |
| `CHANGELOG.md` | Version history and notable changes (this file) |
| `SETUP_GUIDE.md` | Detailed installation and configuration instructions |
| `AGENTS.md` | Agent-specific documentation and guidelines |

### Documentation Guidelines

- **Keep it simple**: One source of truth for each topic
- **Update as you go**: Document features when they're added
- **Remove obsolete docs**: Delete outdated or redundant files
- **Link from README**: Reference detailed guides from the main README
