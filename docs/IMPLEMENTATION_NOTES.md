# Implementation Notes

This document contains technical implementation details for Codemail developers.

## Command Filtering System

### Overview

The command filtering system prevents natural language and markdown content from being executed as bash commands. This is critical because the LLM may include explanations, markdown formatting, or other non-command text in its responses.

### Filter Logic

Commands are validated through multiple checks:

1. **Natural Language Detection**: Patterns that indicate conversational text
2. **Markdown Detection**: Headers, bold text, and other formatting elements
3. **Project Name Detection**: Year-formatted project names like "Bliss (2026)"
4. **Heredoc Exception**: Commands with `<<` heredocs are allowed even if they contain natural language

### Implementation (`llm_interface.py`)

```python
natural_language_indicators = [
    r'^I\s+(don\'t|do\s+not)\s+hav',
    r'^Please\s+clarif',
    r'^To\s+accomplish',
    r'^Once\s+clarifi',
    r'^You\s+are\s+a',
    r'^CRITICAL\s+REQUIREMENTS',
    r'^Bash\s+Command',
    r'^##\s+Summary',
    r'^##\s+Steps',
    r'^##\s+Results',
    r'^##\s+Errors',
]

additional_indicators = [
    r'^markdown$',
    r'^Bliss\s*\(',
    r'^[A-Z][a-z]+\s+\(\d{4}\)$',  # Project name with year
    r'^#{1,6}\s+',                  # Markdown headings
    r'\*\*.*\*\*',                 # Bold markdown text
]
```

### Testing

Run the command filtering tests:

```bash
# Unit tests for filter patterns
python test_command_execution.py

# End-to-end LLM response parsing tests
python test_e2e_filtering.py
```

## Project Workspace Management

### Overview

Each project gets its own isolated workspace directory to prevent interference between tasks.

### Directory Structure

```
projects/
├── default/          # Default workspace (created automatically)
├── my-project/       # Custom project workspace
│   ├── .codemail/    # Task-specific files and logs
│   └── [project files]  # Project source code
```

### Workspace Operations (`workspace_manager.py`)

- `create_project_workspace(name)` - Create workspace directory
- `execute_in_workspace(project, command)` - Execute command in project context
- `cleanup_project_workspace(name)` - Remove task artifacts

## Email Whitelist

### Configuration

Add to `.env`:

```bash
# Sender whitelist (who can submit tasks)
EMAIL_WHITELIST_SENDERS="user@example.com,@domain.com"

# Recipient whitelist (where reports are sent)
EMAIL_WHITELIST_RECIPIENTS="admin@example.com"
```

### Features

- **Multiple addresses**: Comma-separated list
- **Domain wildcards**: Use `@domain.com` to whitelist entire domains
- **Case insensitive**: All comparisons normalized to lowercase

## Task Queue System

### Database Schema (`task_queue.py`)

```python
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    instructions TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed', 'stopped')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result TEXT
)
```

### Status Flow

```
pending → running → completed/failed/stopped
```

## LLM Interface

### Communication (`llm_interface.py`)

The system communicates with local LLM servers using the OpenAI-compatible API format:

```python
# Example request to LM Studio
POST http://127.0.0.1:1234/v1/chat/completions
{
    "model": "local-model",
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    "temperature": 0.7
}
```

### Response Parsing

The LLM interface extracts bash commands from responses using:

1. **Code block detection**: Look for ```bash or ``` markers
2. **Command extraction**: Parse individual command lines
3. **Filtering**: Apply natural language filters
4. **Validation**: Check for valid bash syntax patterns
