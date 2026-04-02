"""
Test script for subject validator functionality.
"""

import sys
sys.path.insert(0, '/home/dev/opencodeprojects/codemail')

from subject_validator import create_subject_validator


def test_valid_codemail_subjects():
    """Test valid codemail subject patterns."""
    validator = create_subject_validator()
    
    test_cases = [
        # Valid cases with prefix
        ("codemail:[my-project] Fix the login bug", True, "my-project", "Fix the login bug"),
        ("CODEMAIL:[My-Project] Add new feature", True, "my-project", "Add new feature"),
        ("Codemail: [test-project] Update documentation", True, "test-project", "Update documentation"),
        ("codemail:[project123] Refactor module X", True, "project123", "Refactor module X"),
    ]
    
    print("Testing valid codemail subjects:")
    for subject, expected_valid, expected_project, expected_instructions in test_cases:
        is_valid, project, instructions = validator.validate_subject(subject)
        
        if is_valid == expected_valid and project == expected_project and instructions == expected_instructions:
            print(f"✓ PASS: '{subject}'")
        else:
            print(f"✗ FAIL: '{subject}'")
            print(f"  Expected: valid={expected_valid}, project='{expected_project}', instructions='{expected_instructions}'")
            print(f"  Got: valid={is_valid}, project='{project}', instructions='{instructions}'")


def test_invalid_subjects():
    """Test invalid subject patterns that should be ignored."""
    validator = create_subject_validator()
    
    test_cases = [
        "Hello, how are you?",
        "Meeting at 3pm",
        "[random] This is not a codemail request",  # Should be rejected - no prefix
        "codemail: no brackets here",
        "RE: codemail:[project] Previous message",
        "",
        None,
    ]
    
    print("\nTesting invalid subjects (should be ignored):")
    for subject in test_cases:
        if subject is None:
            continue
        is_valid, project, instructions = validator.validate_subject(subject)
        
        if not is_valid:
            print(f"✓ PASS: '{subject}' correctly rejected")
        else:
            print(f"✗ FAIL: '{subject}' should have been rejected but got project='{project}'")


def test_custom_prefix():
    """Test with custom prefix."""
    validator = create_subject_validator(prefix="task:")
    
    test_cases = [
        ("task:[my-project] Do something", True, "my-project", "Do something"),
        ("codemail:[my-project] This should fail", False, None, None),
    ]
    
    print("\nTesting custom prefix 'task:':")
    for subject, expected_valid, expected_project, expected_instructions in test_cases:
        is_valid, project, instructions = validator.validate_subject(subject)
        
        if is_valid == expected_valid and project == expected_project and instructions == expected_instructions:
            print(f"✓ PASS: '{subject}'")
        else:
            print(f"✗ FAIL: '{subject}'")
            print(f"  Expected: valid={expected_valid}, project='{expected_project}', instructions='{expected_instructions}'")
            print(f"  Got: valid={is_valid}, project='{project}', instructions='{instructions}'")


def test_is_codemail_request():
    """Test the is_codemail_request convenience method."""
    validator = create_subject_validator()
    
    print("\nTesting is_codemail_request():")
    
    # Valid request
    if validator.is_codemail_request("codemail:[my-project] Fix bug"):
        print("✓ PASS: Valid codemail request detected")
    else:
        print("✗ FAIL: Valid codemail request not detected")
    
    # Invalid request
    if not validator.is_codemail_request("Hello world"):
        print("✓ PASS: Non-codemail request correctly ignored")
    else:
        print("✗ FAIL: Non-codemail request not ignored")


def test_parse_codemail_subject():
    """Test the parse_codemail_subject method."""
    validator = create_subject_validator()
    
    print("\nTesting parse_codemail_subject():")
    
    # Valid subject
    result = validator.parse_codemail_subject("codemail:[my-project] Fix bug")
    if result and result["project_name"] == "my-project" and result["instructions"] == "Fix bug":
        print(f"✓ PASS: Parsed valid subject: {result}")
    else:
        print(f"✗ FAIL: Could not parse valid subject, got: {result}")
    
    # Invalid subject
    result = validator.parse_codemail_subject("Hello world")
    if result is None:
        print("✓ PASS: Invalid subject correctly returned None")
    else:
        print(f"✗ FAIL: Invalid subject should return None, got: {result}")


if __name__ == "__main__":
    test_valid_codemail_subjects()
    test_invalid_subjects()
    test_custom_prefix()
    test_is_codemail_request()
    test_parse_codemail_subject()
    
    print("\n" + "="*50)
    print("Subject validator tests completed!")
