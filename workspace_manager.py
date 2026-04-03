"""
Workspace manager module for Codemail system.
Manages project-specific directories and ensures agent activities are confined to appropriate workspaces.
"""

import os
import shutil
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("codemail.workspace_manager")


class WorkspaceManager:
    """Manages project-specific workspaces for the codemail agent."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize workspace manager.
        
        Args:
            base_dir: Base directory for all project workspaces. Defaults to ./projects
        """
        if base_dir is None:
            # Default to ./projects relative to current working directory
            base_dir = os.path.join(os.getcwd(), "projects")
        
        self.base_dir = os.path.abspath(base_dir)
        self._ensure_base_dir_exists()
        
        logger.info(f"Workspace manager initialized with base dir: {self.base_dir}")
    
    def _ensure_base_dir_exists(self):
        """Ensure the base directory exists."""
        if not os.path.exists(self.base_dir):
            try:
                os.makedirs(self.base_dir, exist_ok=True)
                logger.info(f"Created base workspace directory: {self.base_dir}")
            except Exception as e:
                logger.error(f"Failed to create base workspace directory: {e}")
                raise
    
    def get_project_path(self, project_name: str) -> str:
        """
        Get the path for a project's workspace.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Absolute path to the project workspace
        """
        # Sanitize project name (remove invalid characters)
        sanitized_name = self._sanitize_project_name(project_name)
        return os.path.join(self.base_dir, sanitized_name)
    
    def _sanitize_project_name(self, project_name: str) -> str:
        """
        Sanitize project name for use as directory name.
        
        Args:
            project_name: Original project name
            
        Returns:
            Sanitized project name suitable for filesystem
        """
        # Replace invalid characters with underscores
        import re
        sanitized = re.sub(r'[^\w\-]', '_', project_name)
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Limit length
        return sanitized[:64]
    
    def create_project_workspace(self, project_name: str) -> str:
        """
        Create a workspace directory for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to the created workspace
        """
        project_path = self.get_project_path(project_name)
        
        if not os.path.exists(project_path):
            try:
                os.makedirs(project_path, exist_ok=True)
                logger.info(f"Created workspace for project '{project_name}': {project_path}")
                
                # Create a README file to identify this as a codemail workspace
                readme_path = os.path.join(project_path, "codemail_workspace.txt")
                with open(readme_path, 'w') as f:
                    f.write(f"Codemail Workspace\n")
                    f.write(f"Project: {project_name}\n")
                    f.write(f"Created: {datetime.now().isoformat()}\n")
                    f.write(f"This directory is managed by the codemail agent.\n")
                
            except Exception as e:
                logger.error(f"Failed to create workspace for project '{project_name}': {e}")
                raise
        else:
            logger.info(f"Workspace already exists for project '{project_name}': {project_path}")
        
        return project_path
    
    def cleanup_project_workspace(self, project_name: str) -> bool:
        """
        Clean up a project's workspace (remove all files but keep the directory).
        
        Args:
            project_name: Name of the project
            
        Returns:
            True if cleanup was successful
        """
        project_path = self.get_project_path(project_name)
        
        if not os.path.exists(project_path):
            logger.warning(f"Workspace for project '{project_name}' does not exist")
            return False
        
        try:
            # Remove all files and subdirectories
            for item in os.listdir(project_path):
                item_path = os.path.join(project_path, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            logger.info(f"Cleaned up workspace for project '{project_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup workspace for project '{project_name}': {e}")
            return False
    
    def get_workspace_for_task(self, task: Dict[str, Any]) -> str:
        """
        Get or create workspace for a task's project.
        
        Args:
            task: Task dictionary with 'project_name' field
            
        Returns:
            Path to the project workspace
        """
        project_name = task.get('project_name', 'default')
        return self.create_project_workspace(project_name)
    
    def execute_in_workspace(self, project_name: str, command: str) -> Dict[str, Any]:
        """
        Execute a bash command in the project's workspace directory.
        
        Args:
            project_name: Name of the project
            command: Bash command to execute
            
        Returns:
            Dictionary with execution results (stdout, stderr, returncode)
        """
        import subprocess
        
        project_path = self.get_project_path(project_name)
        
        # Ensure workspace exists
        if not os.path.exists(project_path):
            self.create_project_workspace(project_name)
        
        try:
            logger.info(f"Executing command in workspace '{project_name}': {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command,
                "workspace": project_path,
                "timestamp": datetime.now().isoformat()
            }
            
            if result.returncode == 0:
                logger.info(f"Command executed successfully in '{project_name}'")
            else:
                logger.warning(f"Command failed with return code {result.returncode}: {result.stderr}")
            
            return output
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after 300 seconds: {command}"
            logger.error(error_msg)
            return {
                "stdout": "",
                "stderr": error_msg,
                "returncode": -1,
                "command": command,
                "workspace": project_path,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(error_msg)
            return {
                "stdout": "",
                "stderr": error_msg,
                "returncode": -1,
                "command": command,
                "workspace": project_path,
                "timestamp": datetime.now().isoformat()
            }


def create_workspace_manager(base_dir: str = None):
    """Factory function to create workspace manager."""
    return WorkspaceManager(base_dir)
