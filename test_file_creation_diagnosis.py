#!/usr/bin/env python3
"""
Test script for file creation diagnosis improvements.
Creates test scenarios and verifies enhanced logging works correctly.
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.getcwd())

import logging

# Configure logging to see the enhanced messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("codemail.test")


def create_test_task_result(project_name="test_project", missing_files=None):
    """
    Create a test task result that simulates the file creation scenario.
    
    Args:
        project_name: Name of the test project
        missing_files: List of files that should be "missing"
        
    Returns:
        Path to the test task result file
    """
    # Create temporary workspace
    temp_dir = tempfile.mkdtemp(prefix="codemail_test_")
    project_path = os.path.join(temp_dir, project_name)
    os.makedirs(project_path, exist_ok=True)
    
    # Create some files (but not all expected ones)
    existing_files = ["README.md", "config.json"]
    for f in existing_files:
        with open(os.path.join(project_path, f), 'w') as file:
            file.write(f"# {f}\nTest content\n")
    
    # Determine missing files
    if missing_files is None:
        missing_files = ["AGENTS.md", "docs/README.md"]
    
    # Create bash results showing command execution
    bash_results = []
    
    for filename in missing_files:
        # Simulate a file creation command that was executed but didn't work
        bash_results.append({
            "command": f"cat > {filename} << 'EOF'\n# Test content\nEOF",
            "result": {
                "stdout": "",
                "stderr": "Error: Permission denied or path doesn't exist",
                "returncode": 1
            }
        })
    
    # Add a successful command for comparison
    bash_results.append({
        "command": "ls -la",
        "result": {
            "stdout": "\n".join(existing_files),
            "stderr": "",
            "returncode": 0
        }
    })
    
    # Create task result
    task_result = {
        "task_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "completed",
        "project_name": project_name,
        "workspace_path": project_path,
        "instructions": f"Create files: {', '.join(missing_files)} with documentation.",
        "output": "Task completed successfully.",
        "bash_commands": [r["command"] for r in bash_results],
        "bash_results": bash_results,
        "started_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat()
    }
    
    # Save task result
    temp_file = os.path.join(temp_dir, f"task_result_{project_name}.json")
    with open(temp_file, 'w') as f:
        json.dump(task_result, f, indent=2)
    
    logger.info(f"Created test task result: {temp_file}")
    logger.info(f"Project path: {project_path}")
    logger.info(f"Existing files: {existing_files}")
    logger.info(f"Missing files: {missing_files}")
    
    return temp_file


def test_diagnostic_script(task_file):
    """
    Test the diagnostic script with a task result file.
    
    Args:
        task_file: Path to the task result JSON file
    """
    logger.info("=" * 80)
    logger.info("TESTING DIAGNOSTIC SCRIPT")
    logger.info("=" * 80)
    
    # Import and run diagnostic
    from diagnose_file_creation import analyze_task_result, generate_diagnostic_report
    
    # Analyze the task result
    diagnostics = analyze_task_result(task_file)
    
    logger.info(f"\nDiagnostics Summary:")
    logger.info(f"  Task ID: {diagnostics.get('task_id')}")
    logger.info(f"  Status: {diagnostics.get('status')}")
    logger.info(f"  Expected Files: {diagnostics.get('files_expected')}")
    logger.info(f"  Missing Files: {diagnostics.get('missing_files')}")
    
    # Generate full report
    report = generate_diagnostic_report(task_file)
    
    logger.info("\n" + "=" * 80)
    logger.info("DIAGNOSTIC REPORT:")
    logger.info("=" * 80)
    logger.info(report[:1000])  # Print first 1000 chars
    logger.info("...")
    
    return diagnostics


def test_workspace_analysis(project_name, temp_dir):
    """
    Test workspace state analysis.
    
    Args:
        project_name: Name of the project to analyze
        temp_dir: Temporary directory containing the project
    """
    logger.info("=" * 80)
    logger.info("TESTING WORKSPACE ANALYSIS")
    logger.info("=" * 80)
    
    from diagnose_file_creation import analyze_workspace_state
    
    workspace_path = os.path.join(temp_dir, project_name)
    analysis = analyze_workspace_state(project_name, temp_dir)
    
    logger.info(f"\nWorkspace Analysis:")
    logger.info(f"  Project: {analysis.get('project_name')}")
    logger.info(f"  Path: {analysis.get('workspace_path')}")
    logger.info(f"  Exists: {analysis.get('exists')}")
    logger.info(f"  Files: {[f['name'] for f in analysis.get('files', [])]}")
    
    if analysis.get('permissions'):
        perms = analysis['permissions']
        logger.info(f"  Permissions:")
        logger.info(f"    Readable: {perms.get('readable')}")
        logger.info(f"    Writable: {perms.get('writable')}")
        logger.info(f"    Executable: {perms.get('executable')}")


def main():
    """Run all tests."""
    logger.info("Starting file creation diagnosis tests...")
    
    # Test 1: Create test scenario
    logger.info("\n### TEST 1: Creating test scenario ###")
    task_file = create_test_task_result(
        project_name="test_missing_files",
        missing_files=["AGENTS.md", "docs/README.md"]
    )
    
    # Test 2: Run diagnostic script
    logger.info("\n### TEST 2: Running diagnostic script ###")
    diagnostics = test_diagnostic_script(task_file)
    
    # Verify diagnostics found the issues
    assert diagnostics.get('missing_files'), "Diagnostics should find missing files"
    assert len(diagnostics['missing_files']) > 0, "Should have at least one missing file"
    logger.info("✅ Test 2 passed: Diagnostics correctly identified missing files")
    
    # Test 3: Workspace analysis
    logger.info("\n### TEST 3: Testing workspace analysis ###")
    temp_dir = os.path.dirname(task_file)
    test_workspace_analysis("test_missing_files", temp_dir)
    logger.info("✅ Test 3 passed: Workspace analysis completed")
    
    # Cleanup
    logger.info("\n### CLEANUP ###")
    try:
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to cleanup: {e}")
    
    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
