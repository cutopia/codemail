# Example Enhanced Error Reports

This document shows what users will now receive when tasks fail, with comprehensive diagnostic information.

## Scenario 1: Permission Denied Error

### What Happened
The agent tried to create a file but didn't have write permissions in the workspace directory.

### Email Report Received:

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
      Error: sh: 1: cannot create AGENTS.md: Permission denied

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
[truncated preview - shows what the LLM was asked to do]
```

### How to Fix
- Check workspace directory permissions: `ls -la /home/dev/projects/test-project`
- Ensure the agent has write access to the project directory
- Consider running with appropriate user privileges

---

## Scenario 2: Directory Doesn't Exist

### What Happened
The agent tried to create a file in a subdirectory that doesn't exist.

### Email Report Received:

```
Task ID: abc123-def456-7890
Status: FAILED
Completed: 2026-04-09 23:15:30

## Summary

Task failed to complete.

## Error:
Expected files were not created: src/main.py, docs/README.md

## Diagnostic Information:

### File Status:
- `src/main.py`: ❌ MISSING
  Attempts to create:
    - Command: `cat > src/main.py << 'EOF'`
      Error: cat: can't create 'src/main.py': No such file or directory

- `docs/README.md`: ❌ MISSING
  Attempts to create:
    - Command: `cat > docs/README.md << 'EOF'`
      Error: cat: can't create 'docs/README.md': No such file or directory

### Bash Command Results:
### Command 1: `ls -la /home/dev/projects/myproject` ✅
**STDOUT:**
total 4
drwxr-xr-x 2 user user 4096 Apr  9 23:15 .
drwxr-xr-x 5 user user 4096 Apr  9 23:15 ..

### Command 2: `cat > src/main.py << 'EOF'` ❌ (exit code: 1)
**STDERR:**
cat: can't create 'src/main.py': No such file or directory

### Command 3: `cat > docs/README.md << 'EOF'` ❌ (exit code: 1)
**STDERR:**
cat: can't create 'docs/README.md': No such file or directory

## Full LLM Response:
[truncated preview - shows what the LLM was asked to do]
```

### How to Fix
- The agent should create directories before creating files in them
- Use `mkdir -p src docs` before attempting file creation
- Or use a single command that creates both directory and file

---

## Scenario 3: Invalid Command Syntax

### What Happened
The LLM generated a bash command with incorrect syntax.

### Email Report Received:

```
Task ID: xyz789-abc123-def456
Status: FAILED
Completed: 2026-04-09 23:16:45

## Summary

Task failed to complete.

## Error:
Expected files were not created: config.json

## Diagnostic Information:

### File Status:
- `config.json`: ❌ MISSING
  Attempts to create:
    - Command: `echo '{"key": "value"}' > config.json`
      Output: (empty)

### Bash Command Results:
### Command 1: `ls -la /home/dev/projects/myproject` ✅
**STDOUT:**
total 4
drwxr-xr-x 2 user user 4096 Apr  9 23:16 .
drwxr-xr-x 5 user user 4096 Apr  9 23:16 ..

### Command 2: `echo '{"key": "value"}' > config.json` ❌ (exit code: 1)
**STDERR:**
sh: 1: syntax error: unexpected end of file

## Full LLM Response:
[truncated preview - shows what the LLM was asked to do]
```

### How to Fix
- The command syntax needs to be corrected
- Use proper quoting for JSON content
- Consider using heredoc format instead: `cat > config.json << 'EOF'...EOF`

---

## Scenario 4: Multiple Files, Some Created Successfully

### What Happened
The agent tried to create multiple files, but only some were created successfully.

### Email Report Received:

```
Task ID: multi123-file456-create789
Status: FAILED
Completed: 2026-04-09 23:17:20

## Summary

Task failed to complete.

## Error:
Expected files were not created: file1.txt, file3.txt

## Diagnostic Information:

### File Status:
- `file1.txt`: ❌ MISSING
  Attempts to create:
    - Command: `cat > file1.txt << 'EOF'`
      Error: No space left on device

- `file2.txt`: ✅ EXISTS (size: 1024 bytes)

- `file3.txt`: ❌ MISSING
  Attempts to create:
    - Command: `echo "content" > file3.txt`
      Output: (empty)

### Bash Command Results:
### Command 1: `ls -la /home/dev/projects/myproject` ✅
**STDOUT:**
total 2048
drwxr-xr-x 2 user user 4096 Apr  9 23:17 .
drwxr-xr-x 5 user user 4096 Apr  9 23:17 ..
-rw-r--r-- 1 user user 1024 Apr  9 23:17 file2.txt

### Command 2: `cat > file1.txt << 'EOF'` ❌ (exit code: 1)
**STDERR:**
No space left on device

### Command 3: `echo "content" > file3.txt` ❌ (exit code: 1)
**STDERR:**

## Full LLM Response:
[truncated preview - shows what the LLM was asked to do]
```

### How to Fix
- Check available disk space: `df -h /home/dev/projects/myproject`
- Free up space or increase storage capacity
- The agent successfully created file2.txt but failed on file1.txt and file3.txt

---

## Scenario 5: LLM Parsing Error

### What Happened
The LLM didn't generate proper bash commands, so no files were actually created.

### Email Report Received:

```
Task ID: parse123-error456-llm789
Status: FAILED
Completed: 2026-04-09 23:18:05

## Summary

Task failed to complete.

## Error:
Expected files were not created: AGENTS.md

## Diagnostic Information:

### File Status:
- `AGENTS.md`: ❌ MISSING
  Attempts to create:
    No creation commands found in execution log

### Bash Command Results:
No bash commands were executed (LLM didn't generate valid bash commands)

## Full LLM Response:
I apologize, but I cannot directly create files. Instead, I'll provide you with the content 
that should be in AGENTS.md:

# Project Documentation
This file contains important information about the project.

To create this file, please use the following command:
cat > AGENTS.md << 'EOF'
# Project Documentation
This file contains important information about the project.
EOF

## Steps Taken
1. Analyzed the task requirements
2. Prepared the documentation content
3. Provided the creation command

## Results
The content for AGENTS.md has been prepared above.

Please copy and execute the provided bash command to create the file.
```

### How to Fix
- This is an LLM parsing issue - the agent needs better prompt engineering
- The LLM should be instructed more strongly to generate actual bash commands
- Consider adding validation to ensure bash commands are actually generated

---

## Key Improvements in These Reports

1. **Immediate visibility**: See exactly which files were expected vs. created
2. **Command details**: View the exact commands that were attempted
3. **Error messages**: Get the full error output from the shell
4. **Exit codes**: Know whether commands succeeded (0) or failed (non-zero)
5. **Context**: See the LLM response to understand what was intended

This comprehensive information makes it much easier to diagnose and fix issues!
