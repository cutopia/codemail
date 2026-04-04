# Codemail - Email-Driven Coding Agent

Codemail is a system that allows you to control a self-hosted LLM and coding agent remotely by sending emails with instructions. The system monitors incoming emails, processes tasks in an agentic loop, and reports back via email.

## Features

- 📧 **Email-based interface** - Send instructions via email
- 🔒 **Built-in security** - Email whitelist for sender/recipient control
- 🔄 **Agentic processing** - LLM-driven task execution with iterative refinement
- 📊 **Task tracking** - Real-time status monitoring and reporting
- ⚡ **Async execution** - Celery-based queue management for concurrent tasks

## Quick Start

### Prerequisites

- Python 3.12+
- Local LLM server (e.g., LM Studio) running on port 1234
- Email account with IMAP/SMTP access

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd codemail

# Install dependencies
pip install -r requirements.txt

# Copy example config and customize
cp .env.example .env
```

### Configuration

Edit `.env` with your settings:

```bash
# Email Server Settings
IMAP_HOST=imap.gmail.com
SMTP_HOST=smtp.gmail.com
EMAIL_ADDRESS=codemail@yourdomain.com
EMAIL_PASSWORD=your_app_password

# Security - Whitelist Configuration
EMAIL_WHITELIST_SENDERS="admin@example.com"
EMAIL_WHITELIST_RECIPIENTS="admin@example.com"

# Codemail Settings
CODEMAIL_PREFIX=codemail:
```

### Running the System

```bash
# Start the main monitoring loop
python main.py
```

## Email Whitelist

Codemail includes a security feature that allows you to control which email addresses can:

1. **Submit tasks** (sender whitelist) - Only whitelisted senders can trigger code execution
2. **Receive reports** (recipient whitelist) - Reports only go to trusted recipients

### Configuration

Add to your `.env` file:

```bash
# Single or multiple email addresses
EMAIL_WHITELIST_SENDERS="user1@example.com,user2@example.org"
EMAIL_WHITELIST_RECIPIENTS="user1@example.com,user2@example.org"

# Or whitelist entire domains
EMAIL_WHITELIST_SENDERS="@example.com"
```

For more details, see [EMAIL_WHITELIST.md](EMAIL_WHITELIST.md).

## Email Format

### Subject Line

```
codemail:project_name
```

Where `project_name` is the name of your project directory.

### Body

The email body should contain your instructions for the coding agent:

```
Implement a function to calculate Fibonacci numbers using memoization.
Create unit tests for the implementation.
Add documentation comments to all functions.
```

## Project Structure

```
codemail/
├── main.py              # Entry point
├── config.py            # Configuration management
├── email_monitor.py     # IMAP email monitoring
├── email_reporter.py    # SMTP email reporting
├── email_parser.py      # Email content parsing
├── agent_loop.py        # Task execution orchestration
├── llm_interface.py     # LLM communication
├── task_queue.py        # Task queue management
├── whitelist.py         # Email whitelist functionality
├── api_server.py        # REST API for status monitoring
├── worker.py            # Celery worker
└── projects/            # Project workspaces (created at runtime)
```

## Security Considerations

1. **Use App Passwords**: Never use your main email password; generate an app-specific password
2. **Enable Whitelist**: Always configure sender and recipient whitelists in production
3. **Local LLM**: Run the LLM server locally to avoid sending sensitive code to external APIs
4. **Network Security**: Use SSL/TLS for IMAP/SMTP connections

## Development

### Running Tests

```bash
# Test whitelist functionality
python test_whitelist.py

# Run integration tests
python test_integration.py
```

### Adding Features

1. Keep the project structure simple and focused
2. Add tests before implementing new features (TDD)
3. Update documentation as you add features
4. Ensure backward compatibility when possible

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the API server
- Uses [Celery](https://docs.celeryproject.org/) for task queue management
- Powered by local LLMs via LM Studio or similar servers
