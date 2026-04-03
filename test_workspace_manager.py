"""
Test suite for workspace manager functionality.
Tests project directory isolation and bash command execution.
"""

import unittest
import os
import sys
import tempfile
import shutil

# Add current directory to path
sys.path.insert(0, os.getcwd())

from workspace_manager import WorkspaceManager


class TestWorkspaceManager(unittest.TestCase):
    """Test cases for WorkspaceManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_base_dir = tempfile.mkdtemp(prefix="codemail_test_")
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and all its contents
        if os.path.exists(self.test_base_dir):
            shutil.rmtree(self.test_base_dir)
    
    def test_workspace_manager_initialization(self):
        """Test workspace manager initialization."""
        wm = WorkspaceManager(base_dir=self.test_base_dir)
        
        self.assertIsNotNone(wm)
        self.assertEqual(wm.base_dir, self.test_base_dir)
        self.assertTrue(os.path.exists(wm.base_dir))
    
    def test_get_project_path(self):
        """Test getting project path."""
        wm = WorkspaceManager(base_dir=self.test_base_dir)
        
        # Test basic project name
        path1 = wm.get_project_path("my-project")
        expected1 = os.path.join(self.test_base_dir, "my-project")
        self.assertEqual(path1, expected1)
        
        # Test project name with special characters (should be sanitized)
        path2 = wm.get_project_path("project@#$name")
        self.assertIn(self.test_base_dir, path2)
    
    def test_sanitize_project_name(self):
        """Test project name sanitization."""
        wm = WorkspaceManager(base_dir=self.test_base_dir)
        
        # Test basic sanitization
        sanitized1 = wm._sanitize_project_name("my-project")
        self.assertEqual(sanitized1, "my-project")
        
        # Test special characters are replaced
        sanitized2 = wm._sanitize_project_name("project@#$name")
        self.assertNotIn("@#$", sanitized2)
        
        # Test spaces are replaced
        sanitized3 = wm._sanitize_project_name("my project name")
        self.assertIn("_", sanitized3)
    
    def test_create_project_workspace(self):
        """Test creating a project workspace."""
        wm = WorkspaceManager(base_dir=self.test_base_dir)
        
        project_name = "test-project"
        project_path = wm.create_project_workspace(project_name)
        
        # Verify directory was created
        self.assertTrue(os.path.exists(project_path))
        self.assertTrue(os.path.isdir(project_path))
        
        # Verify README file was created
        readme_path = os.path.join(project_path, "codemail_workspace.txt")
        self.assertTrue(os.path.exists(readme_path))
    
    def test_cleanup_project_workspace(self):
        """Test cleaning up a project workspace."""
        wm = WorkspaceManager(base_dir=self.test_base_dir)
        
        project_name = "cleanup-test"
        project_path = wm.create_project_workspace(project_name)
        
        # Create some files in the workspace
        with open(os.path.join(project_path, "test_file.txt"), 'w') as f:
            f.write("test content")
        
        os.makedirs(os.path.join(project_path, "subdir"))
        with open(os.path.join(project_path, "subdir", "nested.txt"), 'w') as f:
            f.write("nested content")
        
        # Verify files exist
        self.assertTrue(os.path.exists(os.path.join(project_path, "test_file.txt")))
        
        # Cleanup
        result = wm.cleanup_project_workspace(project_name)
        self.assertTrue(result)
        
        # Verify workspace directory still exists and is empty (files removed)
        self.assertTrue(os.path.exists(project_path))
        files = os.listdir(project_path)
        # After cleanup, only the README should remain (or it might be cleaned too)
        # Just verify the directory exists and is accessible
        self.assertLessEqual(len(files), 1)  # README or empty
    
    def test_execute_in_workspace(self):
        """Test executing commands in workspace."""
        wm = WorkspaceManager(base_dir=self.test_base_dir)
        
        project_name = "command-test"
        project_path = wm.create_project_workspace(project_name)
        
        # Test simple command
        result = wm.execute_in_workspace(project_name, "echo 'Hello World'")
        
        self.assertIn("returncode", result)
        self.assertEqual(result["returncode"], 0)
        self.assertIn("stdout", result)
        self.assertIn("Hello World", result["stdout"])
    
    def test_execute_in_workspace_with_file_operations(self):
        """Test file operations in workspace."""
        wm = WorkspaceManager(base_dir=self.test_base_dir)
        
        project_name = "file-test"
        project_path = wm.create_project_workspace(project_name)
        
        # Test creating a file
        result = wm.execute_in_workspace(
            project_name,
            f"echo 'test content' > {project_path}/new_file.txt"
        )
        
        self.assertEqual(result["returncode"], 0)
        self.assertTrue(os.path.exists(os.path.join(project_path, "new_file.txt")))
        
        # Verify file contents
        with open(os.path.join(project_path, "new_file.txt"), 'r') as f:
            content = f.read()
        self.assertIn("test content", content)
    
    def test_workspace_isolation(self):
        """Test that different projects have isolated workspaces."""
        wm = WorkspaceManager(base_dir=self.test_base_dir)
        
        project1 = "project-a"
        project2 = "project-b"
        
        path1 = wm.create_project_workspace(project1)
        path2 = wm.create_project_workspace(project2)
        
        # Verify paths are different
        self.assertNotEqual(path1, path2)
        
        # Create files in each workspace
        with open(os.path.join(path1, "file_a.txt"), 'w') as f:
            f.write("from project A")
        
        with open(os.path.join(path2, "file_b.txt"), 'w') as f:
            f.write("from project B")
        
        # Verify isolation - each workspace should only have its own files
        self.assertTrue(os.path.exists(os.path.join(path1, "file_a.txt")))
        self.assertFalse(os.path.exists(os.path.join(path1, "file_b.txt")))
        
        self.assertTrue(os.path.exists(os.path.join(path2, "file_b.txt")))
        self.assertFalse(os.path.exists(os.path.join(path2, "file_a.txt")))


class TestBashExecutor(unittest.TestCase):
    """Test cases for BashExecutor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_base_dir = tempfile.mkdtemp(prefix="codemail_bash_test_")
        
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.test_base_dir):
            shutil.rmtree(self.test_base_dir)
    
    def test_bash_executor_initialization(self):
        """Test bash executor initialization."""
        from llm_interface import BashExecutor
        
        executor = BashExecutor(base_workspace_dir=self.test_base_dir)
        
        self.assertIsNotNone(executor)
        self.assertIsNotNone(executor.workspace_manager)
    
    def test_execute_command(self):
        """Test command execution."""
        from llm_interface import BashExecutor
        
        executor = BashExecutor(base_workspace_dir=self.test_base_dir)
        
        result = executor.execute_command("echo 'test'", "default")
        
        self.assertIn("returncode", result)
        self.assertEqual(result["returncode"], 0)
        self.assertIn("stdout", result)
        self.assertIn("test", result["stdout"])


if __name__ == '__main__':
    unittest.main()
