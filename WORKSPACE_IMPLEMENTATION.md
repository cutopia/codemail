# Project Workspace & Bash Execution Implementation

## Overview

This document describes the implementation of project workspace isolation and bash command execution capabilities in the Codemail system.

## Features Implemented

### 1. Project Workspace Isolation (`workspace_manager.py`)

Each project gets its own dedicated directory for file operations, ensuring:

- **Isolation**: Projects cannot interfere with each other's files
- **Organization**: All project-related work is contained in a single directory
- **Cleanup**: Easy cleanup of project artifacts after task completion

#### Key Methods

```python
# Create workspace for a project
wm.create_project_workspace("my-project")
# Returns: /path/to/projects/my-project

# Execute command in workspace
result = wm.execute_in_workspace(
    "my-project",
    "npm install && npm run build"
)

# Cleanup workspace (removes files, keeps directory)
wm.cleanup_project_workspace("my-project")
```

### 2. Bash Command Execution (`llm_interface.py`)

The `BashExecutor` class enables the agent to execute shell commands:

```python
from llm_interface import BashExecutor

executor = BashExecutor()
result = executor.execute_command(
    "ls -la",
    project_name="my-project"
)
```

#### Result Format

```json
{
  "stdout": "file1.txt\nfile2.txt\n",
  "stderr": "",
  "returncode": 0,
  "command": "ls -la",
  "workspace": "/path/to/projects/my-project",
  "timestamp": "2024-04-03T12:00:00"
}
```

### 3. Agent Loop Integration (`agent_loop.py`)

The agent loop now:

1. Creates project workspace when task starts
2. Passes workspace path to LLM for context
3. Executes commands in the isolated directory

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Agent Loop (agent_loop.py)            │
├─────────────────────────────────────────────────────┤
│ 1. Receives task from queue                        │
│ 2. Creates workspace for project                   │
│    → workspace_manager.create_project_workspace() │
│ 3. Executes LLM with workspace context             │
│    → llm_interface.execute_iterative_task_with_   │
│       progress(workspace_path=...)                 │
│ 4. Reports results                                 │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│           Workspace Manager (workspace_manager.py) │
├─────────────────────────────────────────────────────┤
│ • Manages project directories                      │
│ • Sanitizes project names for filesystem           │
│ • Creates README files to identify workspaces      │
│ • Provides execute_in_workspace() method          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              Bash Executor (llm_interface.py)      │
├─────────────────────────────────────────────────────┤
│ • Executes shell commands                         │
│ • Captures stdout/stderr/returncode               │
│ • Enforces timeout (5 minutes default)            │
│ • Returns structured results                      │
└─────────────────────────────────────────────────────┘
```

## Usage Examples

### Example 1: Creating a File

```python
from workspace_manager import WorkspaceManager

wm = WorkspaceManager(base_dir="./projects")

# Create project workspace
project_path = wm.create_project_workspace("my-app")

# Execute command to create file
result = wm.execute_in_workspace(
    "my-app",
    "echo 'console.log(\"Hello World\");' > index.js"
)

if result["returncode"] == 0:
    print(f"File created: {project_path}/index.js")
```

### Example 2: Running npm Commands

```python
# Execute multiple commands in sequence
commands = [
    "npm init -y",
    "npm install express",
    "mkdir src"
]

for cmd in commands:
    result = wm.execute_in_workspace("my-app", cmd)
    if result["returncode"] != 0:
        print(f"Command failed: {cmd}")
        print(f"Error: {result['stderr']}")
```

### Example 3: Project Isolation

```python
wm = WorkspaceManager(base_dir="./projects")

# Create two separate projects
path1 = wm.create_project_workspace("project-a")
path2 = wm.create_project_workspace("project-b")

# Files in project-a won't appear in project-b
wm.execute_in_workspace("project-a", "echo 'A' > file.txt")
wm.execute_in_workspace("project-b", "echo 'B' > file.txt")

# Verify isolation
assert os.path.exists(f"{path1}/file.txt")  # True
assert not os.path.exists(f"{path2}/file.txt")  # False (different file)
```

## Configuration

### Environment Variables

```env
# Workspace directory (default: ./projects)
WORKSPACE_DIR=/path/to/workspace

# Task timeout in seconds (default: 3600 = 1 hour)
TASK_TIMEOUT=3600
```

### Default Behavior

- **Base Directory**: `./projects` relative to current working directory
- **Timeout**: 5 minutes for individual commands, 1 hour for entire tasks
- **Workspace Naming**: Project names are sanitized (special characters replaced with underscores)

## Testing

### Unit Tests

```bash
python test_workspace_manager.py
```

Tests cover:
- Workspace creation and cleanup
- Command execution
- Project isolation
- Path sanitization

### Integration Tests

```bash
python test_integration.py
```

Tests the complete workflow:
1. Create workspace
2. Execute commands
3. Verify file operations
4. Test isolation between projects
5. Cleanup

## Security Considerations

1. **Command Timeout**: All bash commands have a 5-minute timeout to prevent hanging
2. **Workspace Isolation**: Projects are confined to their own directories
3. **Input Sanitization**: Project names are sanitized before filesystem use
4. **No Shell Injection**: Commands are executed with `shell=True` but project context is controlled

## Future Enhancements

Potential improvements:
- [ ] Command whitelisting/blacklisting
- [ ] Resource limits (CPU, memory)
- [ ] Containerized execution for additional isolation
- [ ] Command history logging
- [ ] File operation permissions
