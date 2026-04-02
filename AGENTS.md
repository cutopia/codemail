# Codemail Project Plan

## Philosophy: Simplicity and Clarity
**Keep the project clean, simple, and focused.** As features are added, resist the urge to overcomplicate the structure. A clean project structure enables:
- Faster development and debugging
- Easier onboarding for new contributors
- Reduced maintenance burden
- Clear understanding of system flow

When adding functionality, ask: "Can this be integrated into existing files?" or "Is this complexity truly necessary?" Remove obsolete code and documentation regularly.

## Overview
Codemail is a system that allows users to control a self-hosted LLM and coding agent remotely by sending emails with instructions. The system monitors incoming emails, processes tasks in an agentic loop, and reports back via email.

## Tech Stack

### Core Technologies
- **Python 3.12+** - Primary programming language
- **IMAP/SMTP** - Email monitoring and sending (standard protocols)
- **FastAPI** - Web framework for queue status endpoints
- **Celery** - Task queue management for handling concurrent requests
- **Redis** - In-memory data structure store for task queues and state

### LLM Integration
- **LangChain/LlamaIndex** - LLM orchestration frameworks
- **Local LLM server** LLM is hosted locally with LM Studio on the same machine that will be running codemail. Address is: http://127.0.0.1:1234/v1/models (openai api style)
- **Pydantic** - Data validation using Python type annotations

### Email Processing
- **imaplib** - IMAP protocol for email monitoring
- **smtplib** - SMTP protocol for sending emails
- **email** - Built-in Python email parsing library

### Task Management
- **SQLite/PostgreSQL** - Persistent storage for task queue and history
- **UUID** - Unique task identifiers

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Email Monitor │────▶│  Task Queue      │────▶│  Agent Loop     │
│ (IMAP)          │     │  (Celery/Redis)  │     │  (Agentic)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                        │                      │
         ▼                        ▼                      ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Email Sender  │     │  Task Database   │     │  LLM Interface  │
│ (SMTP)          │     │  (SQLite/PG)     │     │  (LangChain)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Status API     │
│  (FastAPI)      │
└─────────────────┘
```

## Core Components

### 1. Email Monitor
- Monitor email inbox for new messages
- Parses emails to extract project name and instructions
- Creates task entries in queue with unique UUIDs

### 2. Task Queue System
- Manages task priority and ordering
- LLM is only permitted to work on one task at a time.
- Tracks task status (pending, running, completed, failed, stopped)
- Provides task progress tracking

### 3. Agent Loop
- Retrieves tasks from queue when LLM is available
- Executes instructions in iterative loop
- Makes bash calls as needed to complete tasks
- Monitors for completion or stop signals
- Generates comprehensive reports

### 4. Email Reporter
- Sends final report with results (success/failure)
- Includes execution time, output logs, and any errors

### 5. Status Interface
- REST API endpoint for queue status
- Task list with details (ID, status, submitted time)
- Current task progress (duration, steps completed)
- Ability to stop specific tasks by ID

## Development Guidelines

### Iterative Development Approach
1. **Start Simple**: Begin with basic email monitoring and single-task execution
2. **Maintain Runnability**: Ensure the project runs after each development step
3. **Incremental Complexity**: Add features like queue management, concurrency, etc., one at a time
4. **Test Each Component**: Verify functionality before moving to next phase

### Phase 1: Core Email Processing
- Set up basic email monitoring (IMAP)
- Parse incoming emails for instructions
- Implement simple LLM call interface
- Send completion reports via SMTP
- **Runnability**: Can receive an email, process it, and send a report

### Phase 2: Task Queue Foundation
- Add database storage for tasks
- Implement basic task queuing (FIFO)
- Add unique task IDs
- **Runnability**: Tasks are queued and processed sequentially

### Phase 3: Agent Loop Enhancement
- Implement iterative execution loop
- Add bash command execution capability
- Track progress within tasks
- **Runnability**: Can execute multi-step instructions

### Phase 4: Concurrency & Status
- Integrate Celery for task queue management
- Add Redis for state tracking
- Implement status API endpoints
- Add ability to stop tasks
- **Runnability**: Multiple tasks can be queued and monitored

## Coding Agent Guidelines

1. **Always Start with Working Code**: Before adding features, ensure existing functionality works
2. **Test-Driven Development**: Write tests for new functionality before implementation
3. **Configuration Over Code**: Use environment variables for configuration (email credentials, LLM endpoints)
4. **Error Handling**: Implement robust error handling for email parsing and task execution
5. **Logging**: Maintain comprehensive logging for debugging and monitoring
6. **Security**: Never commit sensitive credentials; use .env files with gitignore
7. **Documentation**: Update documentation as features are added

## Project Structure Guidelines

1. **Keep It Simple**: Prioritize minimal, focused files over complex, multi-purpose ones
2. **One Responsibility Per File**: Each file should have a single, well-defined purpose
3. **Avoid Redundancy**: Remove duplicate code or overlapping functionality
4. **Organize Logically**: Group related functionality together (e.g., email-related files in one area)
5. **Remove Unused Code**: Delete obsolete files, commented-out code, and experimental features that aren't being used
6. **Document File Purpose**: Add brief comments at the top of each file explaining its role
7. **Consistent Naming**: Use clear, consistent naming conventions for files and functions
8. **Limit File Count**: When adding new functionality, consider if it can be integrated into existing files rather than creating new ones

## Testing Guidelines

1. **Write Tests First**: Create tests before implementing new features (TDD)
2. **Test Coverage**: Aim for comprehensive coverage of core functionality
3. **Automated Testing**: Run tests regularly during development
4. **Simple Test Structure**: Keep test files organized and easy to understand

## Configuration Requirements

- Email server credentials (IMAP/SMTP)
- LLM endpoint URL and API key/token
- Queue backend connection (Redis)
- Database connection string

## Future Enhancements
- Dashboard for real-time monitoring
- Task history and analytics
