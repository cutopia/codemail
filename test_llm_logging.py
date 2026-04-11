"""
Test script for LLM logging functionality.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set debug logging to true for testing
os.environ['LLM_DEBUG_LOGGING'] = 'true'

from llm_interface import LLMInterface, create_llm_interface

def test_llm_logging():
    """Test that LLM logging works correctly."""
    
    # Create LLM interface with debug logging enabled
    llm = create_llm_interface()
    
    print("\n" + "=" * 80)
    print("Testing LLM Logging Functionality")
    print("=" * 80)
    
    # Test basic request
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one word"}
    ]
    
    print("\nSending test message...")
    response = llm._make_request(messages, max_tokens=50)
    
    if response:
        print(f"\nReceived response: {response}")
    else:
        print("\nNo response received (this is expected if LLM endpoint is not available)")
    
    print("\n" + "=" * 80)
    print("Test completed")
    print("=" * 80)

if __name__ == "__main__":
    test_llm_logging()
