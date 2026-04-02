"""
Test suite for Codemail system components.
Tests email parsing, subject validation, task queue, and LLM interface.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from email_parser import create_email_parser
from llm_interface import create_llm_interface
from task_queue import create_task_queue
from subject_validator import create_subject_validator


def test_subject_validator():
    """Test subject validation functionality."""
    print("Testing Subject Validator...")
    
    validator = create_subject_validator()
    
    # Test valid subjects (instructions are now in body, not subject)
    valid_cases = [
        ("codemail:[my-project]", True, "my-project"),
        ("CODEMAIL:[My-Project]", True, "my-project"),
        ("Codemail: [test-project]", True, "test-project"),
    ]
    
    for subject, expected_valid, expected_project in valid_cases:
        is_valid, project, instructions = validator.validate_subject(subject)
        
        # Instructions should always be None now
        if is_valid == expected_valid and project == expected_project and instructions is None:
            print(f"  ✓ Valid: {subject}")
        else:
            print(f"  ✗ FAIL: {subject} (expected valid={expected_valid}, project={expected_project}, instructions=None)")
    
    # Test invalid subjects
    invalid_cases = [
        "Hello, how are you?",
        "[random] This is not a codemail request",
        "codemail: no brackets here",
        "codemail:[project] with instructions in subject",  # Instructions should not be in subject
    ]
    
    for subject in invalid_cases:
        is_valid, _, _ = validator.validate_subject(subject)
        
        if not is_valid:
            print(f"  ✓ Correctly rejected: {subject}")
        else:
            print(f"  ✗ FAIL: Should have rejected: {subject}")
    
    print("Subject Validator tests completed.\n")


def test_email_parser():
    """Test email parsing functionality."""
    print("Testing Email Parser...")
    
    parser = create_email_parser()
    
    # Test 1: Basic email with codemail prefix (instructions in body)
    email1 = {
        "subject": "codemail:[test-project]",
        "body": "Please implement a simple hello world function.",
        "from": "user@example.com"
    }
    result1 = parser.parse_email(email1)
    print(f"  Test 1 - Codemail format: {'PASS' if result1 else 'FAIL'}")
    
    # Test 2: Email with codemail prefix (instructions in body)
    email2 = {
        "subject": "codemail:[my-app]",
        "body": "Please implement a calculator function.",
        "from": "user@example.com"
    }
    result2 = parser.parse_email(email2)
    print(f"  Test 2 - Codemail prefix: {'PASS' if result2 else 'FAIL'}")
    
    # Test 3: Validation
    is_valid, error = parser.validate_task(result1) if result1 else (False, "None result")
    print(f"  Test 3 - Validation: {'PASS' if is_valid else 'FAIL'}")
    
    print("Email Parser tests completed.\n")


def test_llm_interface():
    """Test LLM interface functionality."""
    print("Testing LLM Interface...")
    
    llm = create_llm_interface()
    
    # Test connection
    connected = llm.check_connection()
    print(f"  Connection test: {'PASS' if connected else 'FAIL (LLM not configured)'}")
    
    if connected:
        # Test simple request
        result = llm.execute_task("Say hello in 5 words or less.")
        print(f"  Simple task execution: {'PASS' if result else 'FAIL'}")
        
        # Test iterative execution
        result2 = llm.execute_iterative_task("Write a function to calculate factorial.", max_iterations=2)
        print(f"  Iterative task execution: {'PASS' if result2 else 'FAIL'}")
    
    print("LLM Interface tests completed.\n")


def test_task_queue():
    """Test task queue functionality."""
    print("Testing Task Queue...")
    
    queue = create_task_queue()
    
    # Clean up any existing test tasks first
    all_tasks = queue.get_all_tasks()
    for task in all_tasks:
        if "test" in task.get("project_name", "").lower():
            queue.delete_task(task["id"])
    
    # Test creating a task
    task_id = queue.create_task(
        project_name="test-project",
        instructions="Implement a test function.",
        sender="user@example.com"
    )
    print(f"  Task creation: {'PASS' if task_id else 'FAIL'}")
    
    # Test getting pending task (get the first pending, not necessarily our new one)
    pending = queue.get_pending_task()
    has_pending = pending is not None
    print(f"  Pending task retrieval: {'PASS' if has_pending else 'FAIL'}")
    
    # Test updating status
    import datetime
    updated = queue.update_task_status(
        task_id=task_id,
        status="running",
        started_at=datetime.datetime.now()
    )
    print(f"  Status update: {'PASS' if updated else 'FAIL'}")
    
    # Test getting all tasks
    all_tasks = queue.get_all_tasks()
    print(f"  Task listing ({len(all_tasks)} tasks): PASS")
    
    # Cleanup
    queue.delete_task(task_id)
    print("  Task cleanup: PASS")
    
    print("Task Queue tests completed.\n")


def test_integration():
    """Test integration of components."""
    print("Testing Integration...")
    
    parser = create_email_parser()
    queue = create_task_queue()
    
    # Simulate email processing (instructions in body, not subject)
    email_data = {
        "subject": "codemail:[integration-test]",
        "body": "Write a Python function that calculates the Fibonacci sequence.",
        "from": "test@example.com"
    }
    
    # Parse email
    parsed = parser.parse_email(email_data)
    print(f"  Email parsing: {'PASS' if parsed else 'FAIL'}")
    
    # Create task
    if parsed:
        task_id = queue.create_task(
            project_name=parsed["project_name"],
            instructions=parsed["instructions"]
        )
        print(f"  Task creation: {'PASS' if task_id else 'FAIL'}")
        
        # Get task
        task = queue.get_task(task_id)
        print(f"  Task retrieval: {'PASS' if task else 'FAIL'}")
    
    print("Integration tests completed.\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Codemail System Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_subject_validator()
        test_email_parser()
        test_llm_interface()
        test_task_queue()
        test_integration()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
