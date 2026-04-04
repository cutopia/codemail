"""
Test that email parser uses correct sender field (extracted email, not full From).
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from email_parser import create_email_parser


def test_parser_uses_extracted_email():
    """Test that parser extracts sender_email instead of from field."""
    print("Testing email parser sender extraction...")
    
    # Set up whitelist with cutopia@gmail.com
    os.environ["EMAIL_WHITELIST_SENDERS"] = "cutopia@gmail.com"
    os.environ["EMAIL_WHITELIST_RECIPIENTS"] = "cutopia@gmail.com"
    
    parser = create_email_parser()
    
    # Test email data with full From field - subject must match pattern: codemail:[project-name]
    email_data = {
        "from": "Suzanne <cutopia@gmail.com>",
        "sender_email": "cutopia@gmail.com",
        "subject": "codemail:[default]",
        "body": "Please implement a new feature"
    }
    
    parsed = parser.parse_email(email_data)
    
    print(f"Full From field: {email_data['from']}")
    print(f"Extracted email: {email_data['sender_email']}")
    print(f"Parsed sender: {parsed.get('sender')}")
    
    # The parsed data should use the extracted email, not the full From field
    assert parsed.get("sender") == "cutopia@gmail.com", \
        f"Expected 'cutopia@gmail.com', got '{parsed.get('sender')}'"
    
    print("✓ Parser correctly uses sender_email instead of from field")


def test_parser_with_plain_email():
    """Test parser with plain email address (no name)."""
    print("\nTesting parser with plain email...")
    
    parser = create_email_parser()
    
    email_data = {
        "from": "john@example.com",
        "sender_email": "john@example.com",
        "subject": "codemail:[project]",
        "body": "Do something"
    }
    
    parsed = parser.parse_email(email_data)
    
    assert parsed.get("sender") == "john@example.com", \
        f"Expected 'john@example.com', got '{parsed.get('sender')}'"
    
    print("✓ Parser works correctly with plain email")


def test_parser_with_quoted_name():
    """Test parser with quoted name in From field."""
    print("\nTesting parser with quoted name...")
    
    parser = create_email_parser()
    
    email_data = {
        "from": '"John Smith" <john@example.com>',
        "sender_email": "john@example.com",
        "subject": "codemail:[project]",
        "body": "Do something"
    }
    
    parsed = parser.parse_email(email_data)
    
    assert parsed.get("sender") == "john@example.com", \
        f"Expected 'john@example.com', got '{parsed.get('sender')}'"
    
    print("✓ Parser works correctly with quoted name")


if __name__ == "__main__":
    try:
        test_parser_uses_extracted_email()
        test_parser_with_plain_email()
        test_parser_with_quoted_name()
        
        print("\n" + "=" * 60)
        print("All parser sender tests passed! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
