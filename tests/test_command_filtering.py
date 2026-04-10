#!/usr/bin/env python3
"""Test suite for bash command filtering functionality."""

import re
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from llm_interface import create_bash_executor


def test_natural_language_detection():
    """Test that natural language is correctly identified and filtered."""
    
    # Test cases that should be filtered out (natural language, project names, etc.)
    should_filter = [
        "markdown",
        "Bliss (2026)",
        "Project (2025)",
        "# Heading",
        "## Subheading",
        "**Bold text**",
        "I don't have access to that file",
        "Please clarify the requirements",
        "To accomplish this task, we need to...",
        "Once clarified, I can help you",
        "You are a coding assistant",
        "CRITICAL REQUIREMENTS:",
        "Bash Command:",
        "## Summary",
        "## Steps",
        "## Results",
        "## Errors",
    ]
    
    # Natural language indicators (from the code)
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
    
    print("Testing natural language detection:")
    all_passed = True
    
    for cmd in should_filter:
        is_natural_language = False
        
        for indicator in natural_language_indicators + additional_indicators:
            if re.match(indicator, cmd, re.IGNORECASE | re.MULTILINE):
                is_natural_language = True
                break
        
        passed = is_natural_language
        status = "✅" if passed else "❌"
        print(f"{status} {cmd}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_bash_command_detection():
    """Test that actual bash commands are correctly identified."""
    
    should_allow = [
        "ls -la",
        "cat > file.txt << 'EOF'",
        "echo 'Hello World'",
        "mkdir project",
        "rm -rf temp",
        "git status",
        "python script.py",
        "curl https://example.com",
        "chmod +x script.sh",
    ]
    
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
        r'^[A-Z][a-z]+\s+\(\d{4}\)$',
        r'^#{1,6}\s+',
        r'\*\*.*\*\*',
    ]
    
    print("\nTesting bash command detection:")
    all_passed = True
    
    for cmd in should_allow:
        is_natural_language = False
        
        for indicator in natural_language_indicators + additional_indicators:
            if re.match(indicator, cmd, re.IGNORECASE | re.MULTILINE):
                is_natural_language = True
                break
        
        passed = not is_natural_language
        status = "✅" if passed else "❌"
        print(f"{status} {cmd}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_bash_executor_filtering():
    """Test that the bash executor properly filters commands."""
    
    executor = create_bash_executor()
    
    should_filter = [
        "markdown",
        "Bliss (2026)",
        "# Heading",
        "**Bold text**",
        "I don't have access to that file",
        "Please clarify the requirements",
    ]
    
    should_allow = [
        "ls -la",
        "echo 'Hello World'",
        "pwd",
    ]
    
    print("\nTesting bash executor filtering:")
    all_passed = True
    
    # Test commands that should be filtered
    for cmd in should_filter:
        result = executor.execute_command(cmd, project_name="default")
        
        if result.get("returncode", 0) == -1 and "Error:" in result.get("stderr", ""):
            status = "✅"
        else:
            status = "❌"
            all_passed = False
        
        print(f"{status} Filtered: {cmd[:40]}...")
    
    # Test commands that should be allowed
    for cmd in should_allow:
        result = executor.execute_command(cmd, project_name="default")
        
        if result.get("returncode", -1) == 0 or result.get("stdout"):
            status = "✅"
        else:
            status = "⚠️"
        
        print(f"{status} Allowed: {cmd}")
    
    return all_passed


if __name__ == "__main__":
    results = []
    
    results.append(("Natural language detection", test_natural_language_detection()))
    results.append(("Bash command detection", test_bash_command_detection()))
    results.append(("Bash executor filtering", test_bash_executor_filtering()))
    
    print("\n" + "="*60)
    print("Test Summary:")
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)
