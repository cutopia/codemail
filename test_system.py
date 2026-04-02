"""
Test script for Codemail system components.
Tests each module independently before integration.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from email_parser import create_email_parser
from llm_interface import create_llm_interface
from task_queue import create_task_queue


def test_email_parser():
    """Test email parsing functionality."""
    print("Testing Email Parser...")
    
    parser = create_email_parser()
    
    # Test 1: Basic email with project in brackets
    email1 = {
        "subject": "[test-project] Implement a hello world function",
        "body": "Please implement a simple hello world function.",
        "from": "user@example.com"
    }
    result1 = parser.parse_email(email1)
    print(f"Test 1 - Project in brackets: {result1}")
    
    # Test 2: Email with project header
    email2 = {
        "subject": "Task request",
        "body": "Project: my-app\n\nImplement a calculator function.",
        "from": "user@example.com"
    }
    result2 = parser.parse_email(email2)
    print(f"Test 2 - Project header: {result2}")
    
    # Test 3: Validation
    is_valid, error = parser.validate_task(result1)
    print(f"Validation test: valid={is_valid}, error={error}")
    
    print("Email Parser tests completed.\n")


def test_llm_interface():
    """Test LLM interface functionality."""
    print("Testing LLM Interface...")
    
    llm = create_llm_interface()
    
    # Test connection
    connected = llm.check_connection()
    print(f"LLM Connection test: {'PASSED' if connected else 'FAILED'}")
    
    if connected:
        # Test simple request
        result = llm.execute_task("Say hello in 5 words or less.")
        print(f"Simple task result: {result}")
        
        # Test iterative execution
        result2 = llm.execute_iterative_task("Write a function to calculate factorial.", max_iterations=2)
        print(f"Iterative task result (iterations: {result2.get('iterations')}): {result2['output'][:100]}...")
    
    print("LLM Interface tests completed.\n")


def test_task_queue():
    """Test task queue functionality."""
    print("Testing Task Queue...")
    
    queue = create_task_queue()
    
    # Test creating a task
    task_id = queue.create_task(
        project_name="test-project",
        instructions="Implement a test function.",
        sender="user@example.com"
    )
    print(f"Created task with ID: {task_id}")
    
    # Test getting pending task
    pending = queue.get_pending_task()
    print(f"Pending task: {pending}")
    
    # Test updating status
    import datetime
    queue.update_task_status(
        task_id=task_id,
        status="running",
        started_at=datetime.datetime.now()
    )
    
    # Test getting task by ID
    task = queue.get_task(task_id)
    print(f"Retrieved task: {task}")
    
    # Test completing the task
    queue.update_task_status(
        task_id=task_id,
        status="completed",
        completed_at=datetime.datetime.now(),
        output="Task executed successfully.",
        error=None
    )
    
    # Test getting all tasks
    all_tasks = queue.get_all_tasks()
    print(f"All tasks: {len(all_tasks)} found")
    
    # Cleanup
    queue.delete_task(task_id)
    print("Test task deleted.")
    
    print("Task Queue tests completed.\n")


def test_integration():
    """Test integration of components."""
    print("Testing Integration...")
    
    parser = create_email_parser()
    llm = create_llm_interface()
    queue = create_task_queue()
    
    # Simulate email processing
    email_data = {
        "subject": "[integration-test] Write a simple Python function",
        "body": "Write a Python function that calculates the Fibonacci sequence.",
        "from": "test@example.com"
    }
    
    # Parse email
    parsed = parser.parse_email(email_data)
    print(f"Parsed email: {parsed}")
    
    # Create task
    if parsed:
        task_id = queue.create_task(
            project_name=parsed["project_name"],
            instructions=parsed["instructions"]
        )
        print(f"Created task: {task_id}")
        
        # Get and execute task (simulated)
        task = queue.get_task(task_id)
        print(f"Task details: {task['instructions'][:50]}...")
    
    print("Integration tests completed.\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Codemail System Test Suite")
    print("=" * 60 + "\n")
    
    try:
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
