#!/usr/bin/env python3
"""
Diagnostic script to identify why the agentic loop is stalling.
Run this after a task appears to stall to get detailed diagnostics.
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.getcwd())

from llm_interface import create_llm_interface, create_bash_executor
from agent_loop import AgentLoop
from task_queue import create_task_queue

logger = logging.getLogger("codemail.diagnose")

def check_llm_connection():
    """Check if LLM endpoint is accessible."""
    print("\n" + "="*60)
    print("1. Checking LLM Connection")
    print("="*60)
    
    try:
        llm = create_llm_interface()
        
        # Test basic request
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test' in 5 words or less"}
        ]
        
        print("Sending test request to LLM...")
        response = llm._make_request(messages, max_tokens=20)
        
        if response:
            print(f"✅ LLM responded: '{response}'")
            return True
        else:
            print("❌ LLM returned None - endpoint may be unreachable")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to LLM: {e}")
        return False

def check_bash_execution():
    """Test bash command execution."""
    print("\n" + "="*60)
    print("2. Testing Bash Execution")
    print("="*60)
    
    try:
        executor = create_bash_executor()
        
        # Test simple command
        result = executor.execute_command("echo 'Hello World'", "default")
        
        if result.get("returncode") == 0:
            print(f"✅ Simple command executed: {result['stdout'].strip()}")
            
            # Test ls command (similar to the one in the log)
            result2 = executor.execute_command("ls -la /home/dev/opencodeprojects/codemail/projects", "default")
            
            if result2.get("returncode") == 0:
                print(f"✅ ls command executed successfully")
                return True
            else:
                print(f"❌ ls command failed: {result2.get('stderr', 'No error')}")
                return False
        else:
            print(f"❌ Simple command failed: {result.get('stderr', 'No error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error executing bash commands: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_task_queue():
    """Check task queue status."""
    print("\n" + "="*60)
    print("3. Checking Task Queue Status")
    print("="*60)
    
    try:
        queue = create_task_queue()
        
        # Get pending tasks
        pending = queue.get_pending_task()
        
        if pending:
            print(f"✅ Found pending task: {pending['id']}")
            print(f"   Project: {pending.get('project_name', 'N/A')}")
            print(f"   Status: {pending.get('status', 'N/A')}")
            
            # Get running task
            running = queue.get_running_task()
            
            if running:
                print(f"⚠️  Task {running['id']} is still marked as running")
                return "stuck"
            else:
                print("✅ No tasks currently running")
                return "pending"
        else:
            print("✅ No pending tasks in queue")
            return "empty"
            
    except Exception as e:
        print(f"❌ Error checking task queue: {e}")
        import traceback
        traceback.print_exc()
        return "error"

def check_workspace():
    """Check workspace directories."""
    print("\n" + "="*60)
    print("4. Checking Workspace Directories")
    print("="*60)
    
    try:
        # Check if projects directory exists
        projects_dir = "/home/dev/opencodeprojects/codemail/projects"
        
        if os.path.exists(projects_dir):
            print(f"✅ Projects directory exists: {projects_dir}")
            
            # List subdirectories
            subdirs = [d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]
            
            if subdirs:
                print(f"   Found {len(subdirs)} project directories:")
                for subdir in subdirs[:5]:  # Show first 5
                    print(f"     - {subdir}")
                if len(subdirs) > 5:
                    print(f"     ... and {len(subdirs) - 5} more")
            else:
                print("   ⚠️  No project directories found")
            
            return True
        else:
            print(f"❌ Projects directory does not exist: {projects_dir}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking workspace: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_recent_logs():
    """Check recent log entries."""
    print("\n" + "="*60)
    print("5. Checking Recent Logs")
    print("="*60)
    
    try:
        # Check if there's a log file
        log_files = [
            "/home/dev/opencodeprojects/codemail/codemail.log",
            "codemail.log"
        ]
        
        found_log = None
        for log_file in log_files:
            if os.path.exists(log_file):
                found_log = log_file
                break
        
        if found_log:
            print(f"Found log file: {found_log}")
            
            # Read last 20 lines
            with open(found_log, 'r') as f:
                lines = f.readlines()[-20:]
                
            if lines:
                print("Last 20 log entries:")
                for line in lines:
                    print(f"   {line.rstrip()}")
            else:
                print("Log file exists but is empty")
            
            return True
        else:
            print("⚠️  No log files found - logging may not be configured")
            return False
            
    except Exception as e:
        print(f"Error checking logs: {e}")
        return False

def main():
    """Run all diagnostics."""
    print("="*60)
    print("Codemail Stall Diagnostic Tool")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        "llm_connection": check_llm_connection(),
        "bash_execution": check_bash_execution(),
        "task_queue_status": check_task_queue(),
        "workspace": check_workspace(),
        "logs": check_recent_logs()
    }
    
    print("\n" + "="*60)
    print("Diagnostic Summary")
    print("="*60)
    
    for test, result in results.items():
        if isinstance(result, bool):
            status = "✅ PASS" if result else "❌ FAIL"
        elif result == "stuck":
            status = "⚠️  STUCK"
        elif result == "pending":
            status = "ℹ️  PENDING"
        elif result == "empty":
            status = "ℹ️  EMPTY"
        else:
            status = f"❓ {result}"
        
        print(f"{status}: {test.replace('_', ' ').title()}")
    
    # Determine overall status
    if results["task_queue_status"] == "stuck":
        print("\n⚠️  Task appears to be stuck - check LLM review requests")
        print("   Possible causes:")
        print("   - LLM endpoint not responding")
        print("   - LLM returning empty responses")
        print("   - Network timeout issues")
    elif results["llm_connection"] and results["bash_execution"]:
        print("\n✅ Core components working - issue may be in task-specific logic")
    else:
        print("\n❌ Critical component failure detected")
    
    return results

if __name__ == "__main__":
    main()
