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
        
        # CRITICAL FIX: Validate that the command is actually a bash command, not natural language
        # Skip if it contains natural language patterns
        natural_language_indicators = [
            r'^I\s+(don\'t|do\s+not)\s+hav',
            r'^Please\s+clarif',
            r'^To\s+accomplish',
            r'^Once\s+clarifi',
            r'^You\s+are\s+a',
            r'^CRITICAL\s+REQUIREMENTS',
            r'^Bash\s+Command',
            r'^##\s+Summary',
            r'^##\s+Steps',
            r'^##\s+Results',
            r'^##\s+Errors',
        ]
        
        import re
        for indicator in natural_language_indicators:
            if re.match(indicator, command, re.IGNORECASE | re.MULTILINE):
                logger.warning(f"Skipping natural language response as bash command: {command[:50]}...")
                return {
                    "stdout": "",
                    "stderr": f"Error: Natural language response detected and not executed: {command[:100]}...",
                    "returncode": -1,
                    "command": command,
                    "workspace": self.get_project_path(project_name),
                    "timestamp": datetime.now().isoformat()
                }
        
        # NEW: Additional filtering for non-command text
        additional_indicators = [
            r'^markdown$',
            r'^Bliss\s*\(',
            r'^[A-Z][a-z]+\s+\(\d{4}\)$',  # Project name with year like "Project (2026)"
            r'^#{1,6}\s+',                  # Markdown headings
            r'\*\*.*\*\*',                 # Bold markdown text (anywhere in string)
        ]
        
        for indicator in additional_indicators:
            if re.match(indicator, command, re.IGNORECASE):
                logger.warning(f"Skipping non-bash content as bash command: {command[:50]}...")
                return {
                    "stdout": "",
                    "stderr": f"Error: Non-bash content detected and not executed: {command[:100]}...",
                    "returncode": -1,
                    "command": command,
                    "workspace": self.get_project_path(project_name),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Also check for common LLM response patterns
        if any(phrase in command.lower() for phrase in [
            'i don\'t have',
            'please clarify',
            'to accomplish this',
            'once clarified',
            'you are a coding assistant'
        ]):
            logger.warning(f"Skipping natural language response as bash command: {command[:50]}...")
            return {
                "stdout": "",
                "stderr": f"Error: Natural language response detected and not executed: {command[:100]}...",
                "returncode": -1,
                "command": command,
                "workspace": self.get_project_path(project_name),
                "timestamp": datetime.now().isoformat()
            }
        
        # NEW: Filter out single words that don't look like bash commands
        word_count = len(command.strip().split())
        if word_count == 1:
            cmd_lower = command.lower().strip()
            valid_command_prefixes = [
                'ls', 'cd', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv',
                'git', 'python', 'node', 'npm', 'curl', 'wget', 'chmod',
                'pwd', 'whoami', 'date', 'time', 'sleep', 'test', 'true', 'false'
            ]
            if not any(cmd_lower.startswith(prefix) for prefix in valid_command_prefixes):
                logger.warning(f"Skipping non-command single word: {command[:50]}...")
                return {
                    "stdout": "",
                    "stderr": f"Error: Single word detected and not executed (not a recognized command): {command[:100]}...",
                    "returncode": -1,
                    "command": command,
                    "workspace": self.get_project_path(project_name),
                    "timestamp": datetime.now().isoformat()
                }
        
        project_path = self.get_project_path(project_name)
        
        # Ensure workspace exists
        if not os.path.exists(project_path):
            self.create_project_workspace(project_name)
        
        try:
            logger.info(f"Executing command in workspace '{project_name}': {command}")
            
            logger.info(f"Executing in workspace '{project_name}': {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # CRITICAL FIX: Enhanced file creation verification with detailed logging
            if 'cat >' in command or 'echo >' in command:
                import re
                # Try heredoc pattern first, then simple redirection
                match = re.search(r'(?:cat|echo)\s+>[^\n]*?["\']?([^"\'\n<>|;\s]+)["\']?', command)
                if not match:
                    # For echo "content" > file.txt format
                    match = re.search(r'>(?:\s+|\s*"[^"]*"\s*)?([^"\'\n<>|;\s]+)', command)
                if match:
                    filename = match.group(1).strip()
                    filepath = os.path.join(project_path, filename)
                    
                    # Enhanced logging with workspace context
                    logger.info(f"File creation command executed: {filename}")
                    logger.info(f"  Command: {command[:80]}...")
                    logger.info(f"  Workspace: {project_path}")
                    logger.info(f"  Expected path: {filepath}")
                    
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        logger.info(f"✅ File created successfully: {filename} ({size} bytes)")
                    else:
                        # CRITICAL FIX: Log additional diagnostic info for failed file creation
                        logger.warning(f"❌ Command executed but file may not exist: {filename}")
                        logger.warning(f"  Workspace exists: {os.path.exists(project_path)}")
                        if os.path.exists(project_path):
                            logger.warning(f"  Files in workspace: {os.listdir(project_path)}")
                        logger.warning(f"  Return code: {result.returncode}")
                        logger.warning(f"  Stderr: {result.stderr[:200]}")
            
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
