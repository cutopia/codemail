#!/usr/bin/env python3
"""Test script to verify command filtering works correctly."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from llm_interface import create_bash_executor

def test_command_filtering():
    """Test that the bash executor filters out non-bash commands."""
    
    executor = create_bash_executor()
    
    # Test cases that should be filtered out
    should_filter = [
        "markdown",
        "Bliss (2026)",
        "# Heading",
        "**Bold text**",
        "I don't have access to that file",
        "Please clarify the requirements",
    ]
    
    # Test cases that should be allowed
    should_allow = [
        "ls -la",
        "echo 'Hello World'",
        "pwd",
    ]
    
    print("Testing commands that should be filtered out:")
    for cmd in should_filter:
        result = executor.execute_command(cmd, project_name="default")
        
        if result.get("returncode", 0) == -1 and "Error:" in result.get("stderr", ""):
            status = "✅ FILTERED"
        else:
            status = "❌ NOT FILTERED (ERROR!)"
        
        print(f"{status}: {cmd}")
        if status.startswith("❌"):
            print(f"   Result: {result}")
    
    print("\nTesting commands that should be allowed:")
    for cmd in should_allow:
        result = executor.execute_command(cmd, project_name="default")
        
        # For valid commands, we expect returncode 0 or some output
        if result.get("returncode", -1) == 0 or result.get("stdout"):
            status = "✅ ALLOWED"
        else:
            status = "⚠️  EXECUTED (might have failed for other reasons)"
        
        print(f"{status}: {cmd}")
    
    print("\n" + "="*60)
    print("Test complete!")

if __name__ == "__main__":
    test_command_filtering()
