"""
Integration test for codemail system.
Tests the complete workflow from email processing to task execution.
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.getcwd())

from workspace_manager import WorkspaceManager


def test_complete_workflow():
    """Test a complete workflow with workspace isolation."""
    
    # Create temporary test directory
    test_base_dir = tempfile.mkdtemp(prefix="codemail_integration_")
    
    try:
        print(f"Testing in: {test_base_dir}")
        
        # Initialize workspace manager
        wm = WorkspaceManager(base_dir=test_base_dir)
        
        # Test 1: Create project workspace
        print("\n=== Test 1: Project Workspace Creation ===")
        project_name = "my-test-project"
        project_path = wm.create_project_workspace(project_name)
        print(f"✓ Created workspace at: {project_path}")
        assert os.path.exists(project_path), "Workspace directory should exist"
        
        # Test 2: Execute bash command in workspace
        print("\n=== Test 2: Bash Command Execution ===")
        result = wm.execute_in_workspace(
            project_name,
            "echo 'Hello from codemail!' > hello.txt && ls -la"
        )
        print(f"Command output:\n{result['stdout']}")
        assert result["returncode"] == 0, "Command should succeed"
        
        # Test 3: Verify file was created in workspace
        print("\n=== Test 3: File Creation Verification ===")
        hello_file = os.path.join(project_path, "hello.txt")
        assert os.path.exists(hello_file), "File should exist in workspace"
        with open(hello_file, 'r') as f:
            content = f.read()
        assert "Hello from codemail!" in content, "File content should match"
        print(f"✓ File created successfully: {hello_file}")
        
        # Test 4: Project isolation
        print("\n=== Test 4: Project Isolation ===")
        project2_name = "another-project"
        project2_path = wm.create_project_workspace(project2_name)
        
        # Create a file in project2 that shouldn't be in project1
        result = wm.execute_in_workspace(
            project2_name,
            "echo 'Project 2 content' > unique_file.txt"
        )
        assert result["returncode"] == 0, "Command should succeed"
        
        # Verify isolation - project1 should not have project2's file
        project2_unique_file = os.path.join(project2_path, "unique_file.txt")
        project1_has_project2_file = os.path.exists(
            os.path.join(project_path, "unique_file.txt")
        )
        
        assert os.path.exists(project2_unique_file), "Project 2 file should exist"
        assert not project1_has_project2_file, "Project 1 should not have Project 2's files"
        print("✓ Projects are properly isolated")
        
        # Test 5: Cleanup
        print("\n=== Test 5: Workspace Cleanup ===")
        cleanup_result = wm.cleanup_project_workspace(project_name)
        assert cleanup_result, "Cleanup should succeed"
        print(f"✓ Cleaned up workspace for {project_name}")
        
        print("\n=== All Integration Tests Passed! ===")
        return True
        
    finally:
        # Cleanup test directory
        if os.path.exists(test_base_dir):
            shutil.rmtree(test_base_dir)
            print(f"\nCleaned up test directory: {test_base_dir}")


if __name__ == "__main__":
    success = test_complete_workflow()
    sys.exit(0 if success else 1)
