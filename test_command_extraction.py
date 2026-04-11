#!/usr/bin/env python3
"""
Test script to diagnose bash command extraction issues.
"""

import sys
import os

sys.path.insert(0, os.getcwd())

from llm_interface import LLMInterface

# Create an instance (won't actually connect to LLM)
llm = LLMInterface()

# Test cases that should be extracted as valid commands
test_cases = [
    # Valid bash commands in code blocks
    ("```bash\ncat > AGENTS.md << 'EOF'\n# Project Documentation\nContent here...\nEOF\n```", ["cat > AGENTS.md << 'EOF'"]),
    
    # Simple echo command
    ('```bash\necho "Hello World" > test.txt\n```', ['echo "Hello World" > test.txt']),
    
    # Multiple commands
    ("```bash\nls -la\nmkdir -p docs\n```", ["ls -la", "mkdir -p docs"]),
    
    # Heredoc with content
    ("```bash\ncat > README.md << 'EOF'\n# Title\nContent here.\nEOF\n```", ["cat > README.md << 'EOF'"]),
]

print("Testing bash command extraction...")
print("=" * 80)

for i, (text, expected) in enumerate(test_cases, 1):
    print(f"\n### Test Case {i} ###")
    print(f"Input: {text[:100]}...")
    
    commands = llm._extract_bash_commands(text)
    
    print(f"Expected: {expected}")
    print(f"Extracted: {commands}")
    
    if set(commands) == set(expected):
        print("✅ PASS")
    else:
        print("❌ FAIL - Commands not extracted correctly")

print("\n" + "=" * 80)

# Test the specific case from the error
error_case = """TASK_COMPLETE."""

print(f"\nTesting LLM response: '{error_case}'")
commands = llm._extract_bash_commands(error_case)
print(f"Extracted commands: {commands}")
if not commands:
    print("⚠️  WARNING: No commands extracted - this is expected for TASK_COMPLETE response")

# Test what happens with a typical file creation instruction
typical_response = """I will create the AGENTS.md file now.

```bash
cat > AGENTS.md << 'EOF'
# Project Documentation

This file contains project documentation.
EOF
```

Now I'll verify it was created:

```bash
ls -la AGENTS.md
cat AGENTS.md
```
"""

print("\n" + "=" * 80)
print("Testing typical LLM response with bash commands...")
commands = llm._extract_bash_commands(typical_response)
print(f"Extracted {len(commands)} command(s):")
for cmd in commands:
    print(f"  - {cmd[:60]}...")
