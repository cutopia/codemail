#!/usr/bin/env python3
"""
Test script to verify report email logging is working correctly.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from agent_loop import create_agent_loop
from task_queue import create_task_queue
from email_reporter import create_email_reporter


def test_sender_logging():
    """Test that sender information is logged correctly."""
    print("Testing sender logging...")
    
    # Create components
    queue = create_task_queue()
    reporter = create_email_reporter()
    
    # Create a test task with sender
    task_id = queue.create_task(
        project_name="test_project",
        instructions="Create a test file",
        sender="test@example.com",
        priority=0
    )
    
    print(f"Created task: {task_id}")
    
    # Retrieve the task and check sender
    task = queue.get_task(task_id)
    if task:
        print(f"Task retrieved successfully")
        print(f"  - ID: {task['id']}")
        print(f"  - Project: {task['project_name']}")
        print(f"  - Sender: {task['sender']}")
        print(f"  - Status: {task['status']}")
        
        # Check if sender is present
        if task.get("sender"):
            print("✓ Sender field is present")
        else:
            print("✗ WARNING: Sender field is empty!")
    else:
        print("✗ Failed to retrieve task")
    
    return task_id


def test_report_sending():
    """Test that report sending is logged."""
    print("\nTesting report sending logging...")
    
    reporter = create_email_reporter()
    
    # Test with a whitelisted recipient
    recipient = "cutopia@gmail.com"  # From .env file
    
    result = {
        "status": "completed",
        "output": "Task completed successfully",
        "error": None,
        "iterations": 1,
        "step_summaries": []
    }
    
    success = reporter.send_task_report(
        recipient=recipient,
        task_id="test-task-id-12345",
        task_data=result
    )
    
    if success:
        print("✓ Report sent successfully")
    else:
        print("✗ Report sending failed (check logs for details)")
    
    return success


if __name__ == "__main__":
    print("=" * 60)
    print("Report Email Logging Test")
    print("=" * 60)
    
    try:
        task_id = test_sender_logging()
        
        # Clean up
        if task_id:
            queue = create_task_queue()
            queue.update_task_status(task_id, "completed", completed_at=None)
        
        test_report_sending()
        
        print("\n" + "=" * 60)
        print("Test complete. Check logs for detailed information.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
