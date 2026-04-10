#!/usr/bin/env python3
"""End-to-end test for command filtering."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from llm_interface import LLMInterface, create_bash_executor

def test_llm_response_parsing():
    """Test that LLM responses with natural language are properly filtered."""
    
    # Simulate an LLM response that contains both commands and natural language
    llm_responses = [
        # Response 1: Contains markdown text in code block
        """
Here's what I'll do:

```markdown
markdown
Bliss (2026)
```

This is the result.
""",
        
        # Response 2: Contains valid command mixed with natural language
        """
I'll execute this command:

```bash
ls -la /home/dev/projects/bliss
```

And then I'll verify the results.
""",
        
        # Response 3: Contains invalid commands
        """
Here are the steps:

```bash
Please clarify the requirements
To accomplish this task, we need to...
```
""",
    ]
    
    llm = LLMInterface()
    executor = create_bash_executor()
    
    print("Testing LLM response parsing with command filtering:")
    print("="*60)
    
    for i, response in enumerate(llm_responses, 1):
        print(f"\nTest {i}:")
        print("-"*40)
        
        # Extract commands from the response
        bash_commands = llm._extract_bash_commands(response)
        
        if not bash_commands:
            print("No commands extracted (this might be expected)")
            continue
        
        print(f"Extracted {len(bash_commands)} command(s):")
        
        for cmd in bash_commands:
            # Validate each command
            result = executor.execute_command(cmd, project_name="default")
            
            if result.get("returncode", 0) == -1 and "Error:" in result.get("stderr", ""):
                status = "❌ FILTERED"
                print(f"  {status}: {cmd[:50]}...")
                print(f"    Reason: {result['stderr'][:80]}...")
            else:
                status = "✅ ALLOWED"
                print(f"  {status}: {cmd[:50]}...")
    
    print("\n" + "="*60)
    print("Test complete!")

if __name__ == "__main__":
    test_llm_response_parsing()
