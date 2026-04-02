#!/usr/bin/env python3
"""
System verification script for Codemail.
Checks that all components are properly configured and working.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from email_parser import create_email_parser
from task_queue import create_task_queue
from llm_interface import create_llm_interface


def verify_environment():
    """Verify environment configuration."""
    print("🔍 Verifying Environment Configuration...")
    
    try:
        from config import (
            email_config,
            llm_config,
            database_config
        )
        
        # Check email configuration
        if not email_config.email_address or email_config.email_address == "your_email@example.com":
            print("⚠️  Email address not configured. Edit .env file.")
        else:
            print(f"✓ Email configured: {email_config.email_address}")
        
        # Check LLM configuration  
        print(f"✓ LLM endpoint: {llm_config.endpoint}")
        
        # Check database configuration
        print(f"✓ Database: {database_config.database_url}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def verify_email_parser():
    """Verify email parser functionality."""
    print("\n📧 Verifying Email Parser...")
    
    try:
        parser = create_email_parser()
        
        # Test 1: Project in brackets
        email1 = {
            "subject": "[test-project] Implement a function",
            "body": "Write a Python function to calculate factorial.",
            "from": "user@example.com"
        }
        result1 = parser.parse_email(email1)
        
        if result1 and result1["project_name"] == "test-project":
            print("✓ Project extraction from brackets works")
        else:
            print("✗ Project extraction failed")
            return False
        
        # Test 2: Project header
        email2 = {
            "subject": "Task request",
            "body": "Project: my-app\n\nImplement a calculator.",
            "from": "user@example.com"
        }
        result2 = parser.parse_email(email2)
        
        if result2 and result2["project_name"] == "my-app":
            print("✓ Project extraction from header works")
        else:
            print("✗ Project header extraction failed")
            return False
        
        # Test 3: Validation
        is_valid, error = parser.validate_task(result1)
        if is_valid:
            print("✓ Task validation works")
        else:
            print(f"✗ Validation failed: {error}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Email parser error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_task_queue():
    """Verify task queue functionality."""
    print("\n📋 Verifying Task Queue...")
    
    try:
        queue = create_task_queue()
        
        # Test 1: Create task
        task_id = queue.create_task(
            project_name="test-project",
            instructions="Test instruction for verification.",
            sender="test@example.com"
        )
        
        if task_id:
            print(f"✓ Task creation works (ID: {task_id[:8]}...)")
        else:
            print("✗ Task creation failed")
            return False
        
        # Test 2: Get pending task
        pending = queue.get_pending_task()
        
        if pending and pending["id"] == task_id:
            print("✓ Pending task retrieval works")
        else:
            print("✗ Pending task retrieval failed")
            return False
        
        # Test 3: Update status
        import datetime
        updated = queue.update_task_status(
            task_id=task_id,
            status="running",
            started_at=datetime.datetime.now()
        )
        
        if updated:
            print("✓ Status update works")
        else:
            print("✗ Status update failed")
            return False
        
        # Test 4: Get all tasks
        all_tasks = queue.get_all_tasks()
        
        if len(all_tasks) >= 1:
            print(f"✓ Task listing works ({len(all_tasks)} tasks found)")
        else:
            print("✗ Task listing failed")
            return False
        
        # Cleanup
        queue.delete_task(task_id)
        print("✓ Task cleanup works")
        
        return True
        
    except Exception as e:
        print(f"✗ Task queue error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_llm_interface():
    """Verify LLM interface functionality."""
    print("\n🤖 Verifying LLM Interface...")
    
    try:
        llm = create_llm_interface()
        
        # Test connection
        connected = llm.check_connection()
        
        if connected:
            print("✓ LLM endpoint is reachable")
            
            # Test simple execution (if connected)
            result = llm.execute_task("Say hello in 5 words.")
            
            if result and result.get("status") == "completed":
                print(f"✓ Simple task execution works: {result['output'][:30]}...")
            else:
                print("⚠️  Task execution returned unexpected result")
                
        else:
            print("⚠️  LLM endpoint not reachable (configure LM Studio)")
            print("   Tasks will fail until LM Studio is configured.")
            
        return True
        
    except Exception as e:
        print(f"✗ LLM interface error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_integration():
    """Verify integration of all components."""
    print("\n🔗 Verifying Integration...")
    
    try:
        from workflow import create_workflow
        
        # Create workflow instance
        workflow = create_workflow()
        
        # Test with sample email
        test_email = {
            "subject": "[integration-test] Write a simple function",
            "body": "Write a Python function that calculates the sum of two numbers.",
            "from": "test@example.com"
        }
        
        task_id = workflow.process_single_email(test_email)
        
        if task_id:
            print(f"✓ End-to-end workflow works (Task ID: {task_id[:8]}...)")
            
            # Verify task was created
            queue = create_task_queue()
            task = queue.get_task(task_id)
            
            if task and task["status"] in ["pending", "running"]:
                print("✓ Task state persisted correctly")
            else:
                print("⚠️  Task state not as expected")
                
        else:
            print("✗ Workflow execution failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Integration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Codemail System Verification")
    print("=" * 60)
    
    results = {
        "Environment": verify_environment(),
        "Email Parser": verify_email_parser(),
        "Task Queue": verify_task_queue(),
        "LLM Interface": verify_llm_interface(),
        "Integration": verify_integration()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {component}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All verification checks passed!")
        print("\nThe system is ready to use.")
        print("\nNext steps:")
        print("1. Configure your email credentials in .env")
        print("2. Set up LM Studio and configure LLM_ENDPOINT")
        print("3. Run: python main.py")
    else:
        print("⚠️  Some verification checks failed.")
        print("\nPlease review the errors above and fix the issues.")
    
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
