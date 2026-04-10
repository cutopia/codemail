# Enhanced Error Reporting for Codemail

## Problem Statement

Previously, when tasks failed (especially file creation failures), the error reports were minimal and didn't provide enough diagnostic information to understand why files weren't created:

```
Task ID: 9bb0f010-e882-4a3b-a3f7-7c76475eea6d
Status: FAILED
Completed: 2026-04-09 23:14:57

## Summary

Task failed to complete.

## Error:
Expected files were not created: AGENTS.md
```

This lack of detail made debugging nearly impossible.

## Solution Overview

We've implemented comprehensive error reporting that captures and presents:

1. **File verification details** - Which files were expected, which exist, which are missing
2. **Bash command execution results** - All commands run with their stdout/stderr
3. **Exit codes and error messages** - Detailed information about failures
4. **LLM response context** - The full LLM output for debugging
5. **File creation attempts** - Specific commands that tried to create missing files

## Changes Made

### 1. Enhanced File Verification in `agent_loop.py`

The file verification logic now captures detailed information:

```python
# For each expected file, we track:
- filename: The expected file name
- expected_path: Full path where it should exist  
- exists: Whether the file actually exists
- size: File size if it exists (in bytes)
- attempts: List of bash commands that tried to create this file
  - command: The exact bash command executed
  - success: Whether the command succeeded (exit code 0)
  - stdout: Standard output from the command
  - stderr: Error output from the command
```

### 2. Improved Bash Command Error Handling in `llm_interface.py`

Bash command failures now include:

- **Exit codes**: Explicit return codes for all commands
- **Comprehensive error messages**: Full stderr output
- **Contextual hints**: For common failure modes (permissions, missing paths, syntax errors)
- **Exception details**: Python exceptions during command execution

### 3. Enhanced Email Report Formatting in `email_reporter.py`

Failed task reports now include:

```
## Error:
Expected files were not created: AGENTS.md

## Diagnostic Information:

### File Status:
- `AGENTS.md`: ❌ MISSING
  Attempts to create:
    - Command: `cat > AGENTS.md << 'EOF'...`
      Error: No such file or directory

### Bash Command Results:
### Command 1: `ls -la /path/to/workspace` ✅
**STDOUT:**
[listing of files]

### Command 2: `cat > AGENTS.md << 'EOF'...` ❌ (exit code: 1)
**STDERR:**
sh: 1: cannot create AGENTS.md: Permission denied

## Full LLM Response:
[truncated preview of the LLM's output]
```

## Example Enhanced Error Report

Here's what a typical enhanced error report looks like:

```
Task ID: 9bb0f010-e882-4a3b-a3f7-7c76475eea6d
Status: FAILED
Completed: 2026-04-09 23:14:57

## Summary

Task failed to complete.

## Error:
Expected files were not created: AGENTS.md

## Diagnostic Information:

### File Status:
- `AGENTS.md`: ❌ MISSING
  Attempts to create:
    - Command: `cat > AGENTS.md << 'EOF'`
      Error: No such file or directory

### Bash Command Results:
### Command 1: `ls -la /home/dev/projects/test-project` ✅
**STDOUT:**
total 8
drwxr-xr-x 2 user user 4096 Apr  9 23:14 .
drwxr-xr-x 5 user user 4096 Apr  9 23:14 ..

### Command 2: `cat > AGENTS.md << 'EOF'` ❌ (exit code: 1)
**STDERR:**
sh: 1: cannot create AGENTS.md: Permission denied

## Full LLM Response:
[truncated preview]
```

## Benefits

1. **Faster debugging**: See exactly what commands were attempted and why they failed
2. **Better user experience**: Users can see the full execution context, not just failure messages
3. **Easier troubleshooting**: No more guessing - all diagnostic information is included
4. **Reduced support burden**: Self-service debugging with comprehensive error reports

## Testing Recommendations

1. Test file creation tasks that should succeed (verify they still work)
2. Test file creation tasks that fail due to permissions (should show detailed errors)
3. Test file creation tasks that fail due to path issues (should show directory structure)
4. Test LLM response parsing failures (should show the full LLM output)

## Future Enhancements

Potential future improvements:

1. **File existence verification**: Add explicit `ls -la filename` commands after file creation
2. **Permission checking**: Pre-flight checks for write permissions in workspace directories
3. **Disk space reporting**: Include available disk space in error reports
4. **Timeline visualization**: Show execution timeline with timestamps for each command
