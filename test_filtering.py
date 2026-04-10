#!/usr/bin/env python3
"""Test script for bash command filtering."""

import re

def test_command_filtering():
    """Test that the filtering logic correctly identifies non-bash commands."""
    
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
    
    # Test cases that should be allowed (actual bash commands)
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
    
    # Additional indicators (new)
    additional_indicators = [
        r'^markdown$',
        r'^Bliss\s*\(',
        r'^[A-Z][a-z]+\s+\(\d{4}\)$',  # Project name with year like "Project (2026)"
        r'^#{1,6}\s+',                  # Markdown headings
        r'\*\*.*\*\*',                 # Bold markdown text (anywhere in string)
    ]
    
    print("Testing commands that should be filtered out:")
    for cmd in should_filter:
        is_natural_language = False
        
        # Check natural language indicators
        for indicator in natural_language_indicators:
            if re.match(indicator, cmd, re.IGNORECASE | re.MULTILINE):
                is_natural_language = True
                break
        
        # Check additional indicators
        if not is_natural_language:
            for indicator in additional_indicators:
                if re.match(indicator, cmd, re.IGNORECASE):
                    is_natural_language = True
                    break
        
        status = "✅ FILTERED" if is_natural_language else "❌ NOT FILTERED"
        print(f"{status}: {cmd}")
    
    print("\nTesting commands that should be allowed:")
    for cmd in should_allow:
        is_natural_language = False
        
        # Check natural language indicators
        for indicator in natural_language_indicators:
            if re.match(indicator, cmd, re.IGNORECASE | re.MULTILINE):
                is_natural_language = True
                break
        
        # Check additional indicators
        if not is_natural_language:
            for indicator in additional_indicators:
                if re.match(indicator, cmd, re.IGNORECASE):
                    is_natural_language = True
                    break
        
        status = "✅ ALLOWED" if not is_natural_language else "❌ FILTERED (ERROR)"
        print(f"{status}: {cmd}")

if __name__ == "__main__":
    test_command_filtering()
