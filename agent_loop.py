"""
Agent loop module for Codemail system.
Orchestrates the execution of tasks using LLM and manages the workflow with robust error handling.
"""

import logging
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List, Any
from email_parser import create_email_parser
from llm_interface import create_llm_interface, create_bash_executor
from task_queue import create_task_queue
from email_reporter import create_email_reporter

logger = logging.getLogger("codemail.agent_loop")


class AgentLoop:
    """Main agent loop that processes tasks from the queue with robust error handling."""
    
    def __init__(self, parser_prefix: str = None):
        # Get prefix from environment if not provided
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        if parser_prefix is None:
            parser_prefix = os.getenv("CODEMAIL_PREFIX", "codemail:")
        
        self.parser = create_email_parser(parser_prefix)
        self.llm = create_llm_interface()
        self.bash_executor = create_bash_executor()
        self.queue = create_task_queue()
        self.reporter = create_email_reporter()
        
        # Configuration
        self.max_retries = int(os.getenv("AGENT_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("AGENT_RETRY_DELAY", "60"))  # seconds
        self.task_timeout = int(os.getenv("TASK_TIMEOUT", "3600"))  # 1 hour default
        
        # Get workspace directory from environment or use default
        self.workspace_dir = os.getenv("WORKSPACE_DIR", os.path.join(os.getcwd(), "projects"))
        
    def process_email(self, email_data: Dict) -> Optional[str]:
        """
        Process a single email and add task to queue.
        
        Args:
            email_data: Dictionary with 'subject', 'body', 'from' keys
            
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            logger.info("Processing incoming email...")
            
            # Parse email content
            parsed_data = self.parser.parse_email(email_data)
            
            if parsed_data is None:
                logger.warning("Email does not match codemail pattern - ignoring")
                return None
            
            if not parsed_data:
                logger.error("Failed to parse email")
                return None
            
            # Validate task data
            is_valid, error_msg = self.parser.validate_task(parsed_data)
            
            if not is_valid:
                logger.error(f"Invalid task: {error_msg}")
                return None
            
            # Create task in queue with priority based on sender
            priority = 0  # Default priority
            if parsed_data.get("sender"):
                # Higher priority for known senders (could be extended)
                priority = 1
                
            task_id = self.queue.create_task(
                project_name=parsed_data["project_name"],
                instructions=parsed_data["instructions"],
                sender=parsed_data.get("sender"),
                priority=priority
            )
            
            logger.info(f"Task created with ID: {task_id} (priority: {priority})")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return None
    
    def execute_task_with_progress(self, task_id: str) -> Dict:
        """
        Execute a single task from the queue with progress tracking.
        
        Args:
            task_id: Unique identifier of the task to execute
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Get task from queue
            task = self.queue.get_task(task_id)
            
            if not task:
                logger.error(f"Task {task_id} not found")
                return {"status": "failed", "error": "Task not found"}
            
            project_name = task.get('project_name', 'default')
            logger.info(f"Executing task {task_id} for project '{project_name}': {task['instructions'][:100]}...")
            
            # Create workspace for the project
            try:
                project_path = self.bash_executor.workspace_manager.create_project_workspace(project_name)
                logger.info(f"Project workspace: {project_path}")
            except Exception as e:
                logger.warning(f"Failed to create workspace: {e}")
                project_path = None
            
            # Check if task has timed out
            created_at = datetime.fromisoformat(task['created_at']) if task.get('created_at') else None
            if created_at:
                age = datetime.now() - created_at
                if age > timedelta(seconds=self.task_timeout):
                    logger.warning(f"Task {task_id} has timed out after {age.total_seconds()}s")
                    return {"status": "failed", "error": f"Task timed out after {self.task_timeout}s"}
            
            # Update status to running with progress tracking
            self.queue.update_task_status(
                task_id=task_id,
                status="running",
                started_at=datetime.now()
            )
            
            # Set initial state in Redis
            if hasattr(self.queue, 'set_task_state'):
                self.queue.set_task_state(task_id, {
                    "status": "running",
                    "message": "Starting execution...",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Execute with LLM and progress tracking (pass project context)
            result = self.llm.execute_iterative_task_with_progress(
                task["instructions"],
                task_id=task_id,
                progress_callback=self._progress_callback,
                max_iterations=int(os.getenv("MAX_ITERATIONS", "5")),
                project_name=project_name,
                workspace_path=project_path,
                bash_executor=self.bash_executor
            )
            
            # CRITICAL FIX: Validate that file operations were actually performed
            if result.get("status") == "completed" and project_path:
                # Check if the task involved file creation (instructions contain keywords)
                instructions_lower = task["instructions"].lower()
                file_keywords = ['create', 'generate', 'write', 'file', '.md', '.txt', '.py', '.json']
                
                if any(keyword in instructions_lower for keyword in file_keywords):
                    # Extract expected filenames from instructions
                    import re
                    # Look for patterns like "AGENTS.md", "README.md", etc.
                    potential_files = re.findall(r'([A-Za-z_]+\.(?:md|txt|py|json))', task["instructions"])
                    
                    if potential_files:
                        missing_files = []
                        file_verification_details = []  # Detailed verification info
                        
                        for filename in potential_files:
                            filepath = os.path.join(project_path, filename)
                            exists = os.path.exists(filepath)
                            
                            # Gather detailed information about the file attempt
                            file_info = {
                                "filename": filename,
                                "expected_path": filepath,
                                "exists": exists,
                                "attempts": []
                            }
                            
                            # Check bash results for attempts to create this file
                            if result.get("bash_results"):
                                for cmd_result in result["bash_results"]:
                                    cmd = cmd_result.get("command", "")
                                    res = cmd_result.get("result", {})
                                    
                                    # Look for commands that might create this file
                                    if filename in cmd and ('cat >' in cmd or 'echo >' in cmd):
                                        file_info["attempts"].append({
                                            "command": cmd,
                                            "success": res.get("returncode", -1) == 0,
                                            "stdout": res.get("stdout", ""),
                                            "stderr": res.get("stderr", "")
                                        })
                            
                            # Check if file exists and get basic info
                            if exists:
                                try:
                                    file_info["size"] = os.path.getsize(filepath)
                                    file_info["modified"] = os.path.getmtime(filepath)
                                except Exception:
                                    pass
                            else:
                                missing_files.append(filename)
                            
                            file_verification_details.append(file_info)
                        
                        if missing_files:
                            logger.warning(f"Task marked complete but files were not created: {missing_files}")
                            
                            # Build comprehensive error message with diagnostic details
                            error_parts = [f"Expected files were not created: {', '.join(missing_files)}"]
                            error_parts.append("\n## File Verification Details:")
                            
                            for file_info in file_verification_details:
                                filename = file_info["filename"]
                                exists = file_info["exists"]
                                
                                if exists:
                                    size = file_info.get("size", "unknown")
                                    error_parts.append(f"- `{filename}`: ✅ EXISTS (size: {size} bytes)")
                                else:
                                    error_parts.append(f"- `{filename}`: ❌ MISSING")
                                    
                                    # Add creation attempts
                                    attempts = file_info.get("attempts", [])
                                    if attempts:
                                        error_parts.append(f"  Attempts to create:")
                                        for attempt in attempts:
                                            cmd = attempt["command"]
                                            success = attempt["success"]
                                            stdout = attempt.get("stdout", "")[:200]  # Truncate long output
                                            stderr = attempt.get("stderr", "")
                                            
                                            error_parts.append(f"    - Command: `{cmd}`")
                                            if not success:
                                                error_parts.append(f"      Error: {stderr[:300]}")  # Show error details
                                            else:
                                                error_parts.append(f"      Output: {stdout[:200]}")
                                    else:
                                        error_parts.append("  No creation commands found in execution log")
                            
                            # Include full bash results for debugging
                            if result.get("bash_results"):
                                error_parts.append("\n## All Bash Commands Executed:")
                                for idx, cmd_result in enumerate(result["bash_results"], 1):
                                    cmd = cmd_result.get("command", "")
                                    res = cmd_result.get("result", {})
                                    returncode = res.get("returncode", -1)
                                    
                                    if returncode == 0:
                                        error_parts.append(f"### Command {idx}: `{cmd}` ✅")
                                    else:
                                        error_parts.append(f"### Command {idx}: `{cmd}` ❌ (exit code: {returncode})")
                                    
                                    stdout = res.get("stdout", "").strip()
                                    stderr = res.get("stderr", "").strip()
                                    
                                    if stdout:
                                        error_parts.append(f"**STDOUT:**\n```\n{stdout[:500]}\n```")  # Truncate
                                    if stderr:
                                        error_parts.append(f"**STDERR:**\n```\n{stderr[:500]}\n```")
                            
                            # Include the full LLM output for context
                            llm_output = result.get("output", "")
                            if llm_output:
                                error_parts.append("\n## Full LLM Response:")
                                error_parts.append(f"```\n{llm_output[:1000]}\n```")  # Truncate to avoid massive emails
                            
                            # Update status and include comprehensive error details
                            result["status"] = "failed"
                            result["error"] = "\n".join(error_parts)
            
            # Update task with results
            completed_at = datetime.now()
            self.queue.update_task_status(
                task_id=task_id,
                status=result["status"],
                completed_at=completed_at,
                output=result.get("output"),
                error=result.get("error")
            )
            
            logger.info(f"Task {task_id} completed with status: {result['status']}")
            
            # Update final state in Redis
            if hasattr(self.queue, 'set_task_state'):
                self.queue.set_task_state(task_id, {
                    "status": result["status"],
                    "message": f"Completed: {result.get('output', '')[:100]}",
                    "timestamp": datetime.now().isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            
            # Update task status to failed
            self.queue.update_task_status(
                task_id=task_id,
                status="failed",
                completed_at=datetime.now(),
                error=str(e)
            )
            
            # Update Redis state for failed task
            if hasattr(self.queue, 'set_task_state'):
                self.queue.set_task_state(task_id, {
                    "status": "failed",
                    "message": f"Error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
            
            return {"status": "failed", "error": str(e)}
    
    def execute_task(self, task_id: str) -> bool:
        """
        Execute a single task from the queue with retry logic.
        
        Args:
            task_id: Unique identifier of the task to execute
            
        Returns:
            True if execution completed successfully, False otherwise
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Get task from queue
                task = self.queue.get_task(task_id)
                
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return False
                
                project_name = task.get('project_name', 'default')
                logger.info(f"Executing task {task_id} for project '{project_name}' (attempt {attempt + 1}/{self.max_retries + 1}): {task['instructions'][:100]}...")
                
                # Create workspace for the project
                try:
                    project_path = self.bash_executor.workspace_manager.create_project_workspace(project_name)
                    logger.info(f"Project workspace: {project_path}")
                except Exception as e:
                    logger.warning(f"Failed to create workspace: {e}")
                    project_path = None
                
                # Update status to running with progress tracking
                self.queue.update_task_status(
                    task_id=task_id,
                    status="running",
                    started_at=datetime.now()
                )
                
                # Set initial state in Redis
                if hasattr(self.queue, 'set_task_state'):
                    self.queue.set_task_state(task_id, {
                        "status": "running",
                        "message": "Starting execution...",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Execute with LLM and progress tracking (pass project context)
                result = self.llm.execute_iterative_task_with_progress(
                    task["instructions"],
                    task_id=task_id,
                    progress_callback=self._progress_callback,
                    max_iterations=int(os.getenv("MAX_ITERATIONS", "5")),
                    project_name=project_name,
                    workspace_path=project_path,
                    bash_executor=self.bash_executor
                )
                
                # Update task with results
                completed_at = datetime.now()
                
                # CRITICAL FIX: Verify that expected files were actually created
                if result.get("status") == "completed" and project_path:
                    # Check if the task involved file creation (instructions contain keywords)
                    instructions_lower = task["instructions"].lower()
                    file_keywords = ['create', 'generate', 'write', 'file', '.md', '.txt', '.py', '.json']
                    
                    if any(keyword in instructions_lower for keyword in file_keywords):
                        # Extract expected filenames from instructions
                        import re
                        # Look for patterns like "AGENTS.md", "README.md", etc.
                        potential_files = re.findall(r'([A-Za-z_]+\.(?:md|txt|py|json))', task["instructions"])
                        
                        if potential_files:
                            missing_files = []
                            file_verification_details = []  # Detailed verification info
                            
                            for filename in potential_files:
                                filepath = os.path.join(project_path, filename)
                                exists = os.path.exists(filepath)
                                
                                # Gather detailed information about the file attempt
                                file_info = {
                                    "filename": filename,
                                    "expected_path": filepath,
                                    "exists": exists,
                                    "attempts": []
                                }
                                
                                # Check bash results for attempts to create this file
                                if result.get("bash_results"):
                                    for cmd_result in result["bash_results"]:
                                        cmd = cmd_result.get("command", "")
                                        res = cmd_result.get("result", {})
                                        
                                        # Look for commands that might create this file
                                        if filename in cmd and ('cat >' in cmd or 'echo >' in cmd):
                                            file_info["attempts"].append({
                                                "command": cmd,
                                                "success": res.get("returncode", -1) == 0,
                                                "stdout": res.get("stdout", ""),
                                                "stderr": res.get("stderr", "")
                                            })
                                
                                # Check if file exists and get basic info
                                if exists:
                                    try:
                                        file_info["size"] = os.path.getsize(filepath)
                                        file_info["modified"] = os.path.getmtime(filepath)
                                    except Exception:
                                        pass
                                else:
                                    missing_files.append(filename)
                                
                                file_verification_details.append(file_info)
                            
                            if missing_files:
                                logger.warning(f"Task marked complete but files were not created: {missing_files}")
                                
                                # Build comprehensive error message with diagnostic details
                                error_parts = [f"Expected files were not created: {', '.join(missing_files)}"]
                                error_parts.append("\n## File Verification Details:")
                                
                                for file_info in file_verification_details:
                                    filename = file_info["filename"]
                                    exists = file_info["exists"]
                                    
                                    if exists:
                                        size = file_info.get("size", "unknown")
                                        error_parts.append(f"- `{filename}`: ✅ EXISTS (size: {size} bytes)")
                                    else:
                                        error_parts.append(f"- `{filename}`: ❌ MISSING")
                                        
                                        # Add creation attempts
                                        attempts = file_info.get("attempts", [])
                                        if attempts:
                                            error_parts.append(f"  Attempts to create:")
                                            for attempt in attempts:
                                                cmd = attempt["command"]
                                                success = attempt["success"]
                                                stdout = attempt.get("stdout", "")[:200]  # Truncate long output
                                                stderr = attempt.get("stderr", "")
                                                
                                                error_parts.append(f"    - Command: `{cmd}`")
                                                if not success:
                                                    error_parts.append(f"      Error: {stderr[:300]}")  # Show error details
                                                else:
                                                    error_parts.append(f"      Output: {stdout[:200]}")
                                        else:
                                            error_parts.append("  No creation commands found in execution log")
                                
                                # Include full bash results for debugging
                                if result.get("bash_results"):
                                    error_parts.append("\n## All Bash Commands Executed:")
                                    for idx, cmd_result in enumerate(result["bash_results"], 1):
                                        cmd = cmd_result.get("command", "")
                                        res = cmd_result.get("result", {})
                                        returncode = res.get("returncode", -1)
                                        
                                        if returncode == 0:
                                            error_parts.append(f"### Command {idx}: `{cmd}` ✅")
                                        else:
                                            error_parts.append(f"### Command {idx}: `{cmd}` ❌ (exit code: {returncode})")
                                        
                                        stdout = res.get("stdout", "").strip()
                                        stderr = res.get("stderr", "").strip()
                                        
                                        if stdout:
                                            error_parts.append(f"**STDOUT:**\n```\n{stdout[:500]}\n```")  # Truncate
                                        if stderr:
                                            error_parts.append(f"**STDERR:**\n```\n{stderr[:500]}\n```")
                                
                                # Include the full LLM output for context
                                llm_output = result.get("output", "")
                                if llm_output:
                                    error_parts.append("\n## Full LLM Response:")
                                    error_parts.append(f"```\n{llm_output[:1000]}\n```")  # Truncate to avoid massive emails
                                
                                # Update status and include comprehensive error details
                                result["status"] = "failed"
                                result["error"] = "\n".join(error_parts)
                
                self.queue.update_task_status(
                    task_id=task_id,
                    status=result["status"],
                    completed_at=completed_at,
                    output=result.get("output"),
                    error=result.get("error")
                )
                
                logger.info(f"Task {task_id} completed with status: {result['status']}")
                
                # Update final state in Redis
                if hasattr(self.queue, 'set_task_state'):
                    self.queue.set_task_state(task_id, {
                        "status": result["status"],
                        "message": f"Completed: {result.get('output', '')[:100]}",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Send report to sender
                if task.get("sender"):
                    self.reporter.send_task_report(
                        recipient=task["sender"],
                        task_id=task_id,
                        task_data=result
                    )
                
                return True
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error executing task {task_id} (attempt {attempt + 1}): {e}")
                
                # Update Redis state for failed attempt
                if hasattr(self.queue, 'set_task_state'):
                    self.queue.set_task_state(task_id, {
                        "status": "running",
                        "message": f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Don't retry if we've exhausted all attempts
                if attempt < self.max_retries:
                    logger.info(f"Retrying task {task_id} in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
        
        # All retries failed - mark as failed
        logger.error(f"Task {task_id} failed after {self.max_retries + 1} attempts. Last error: {last_error}")
        
        self.queue.update_task_status(
            task_id=task_id,
            status="failed",
            completed_at=datetime.now(),
            error=f"Failed after {self.max_retries + 1} attempts. Last error: {last_error}"
        )
        
        if hasattr(self.queue, 'set_task_state'):
            self.queue.set_task_state(task_id, {
                "status": "failed",
                "message": f"Failed after {self.max_retries + 1} attempts",
                "timestamp": datetime.now().isoformat()
            })
        
        return False
    
    def _progress_callback(self, task_id: str, current_step: int, total_steps: int,
                          message: str = "") -> bool:
        """
        Callback function for progress updates during task execution.
        
        Args:
            task_id: Unique identifier of the task
            current_step: Current step number
            total_steps: Total number of steps
            message: Progress message
            
        Returns:
            True if callback executed successfully, False otherwise
        """
        try:
            # Update progress in Redis
            if hasattr(self.queue, 'update_task_progress'):
                self.queue.update_task_progress(task_id, current_step, total_steps, message)
            
            logger.debug(f"Task {task_id} progress: {current_step}/{total_steps} - {message}")
            return True
        except Exception as e:
            logger.error(f"Error in progress callback: {e}")
            return False
    
    def process_queue(self, max_tasks: int = None, priority_only: bool = False) -> int:
        """
        Process all pending tasks in the queue.
        
        Args:
            max_tasks: Maximum number of tasks to process (None for unlimited)
            priority_only: If True, only process high-priority tasks
            
        Returns:
            Number of tasks processed
        """
        from datetime import datetime
        
        processed = 0
        
        while True:
            if max_tasks and processed >= max_tasks:
                break
                
            task = self.queue.get_pending_task(priority_only=priority_only)
            
            if not task:
                logger.info("No pending tasks in queue")
                break
            
            success = self.execute_task(task["id"])
            
            if success:
                processed += 1
            else:
                logger.error(f"Failed to process task {task['id']}")
        
        return processed
    
    def run_loop(self, poll_interval: int = 60):
        """
        Run the agent loop continuously.
        
        Args:
            poll_interval: Seconds between queue checks
        """
        from datetime import datetime
        
        logger.info("Starting agent loop...")
        
        while True:
            try:
                # Process any pending tasks (one at a time for safety)
                processed = self.process_queue(max_tasks=1)
                
                if processed == 0:
                    logger.info(f"No tasks to process. Waiting {poll_interval} seconds...")
                
                # Wait before next check
                import time
                time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Agent loop stopped by user")
                break
                
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                import time
                time.sleep(poll_interval)  # Wait before retrying
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get comprehensive queue status including all metrics.
        
        Returns:
            Dictionary with queue statistics and details
        """
        try:
            stats = self.queue.get_queue_stats()
            
            # Get running task if any
            running_task = None
            if hasattr(self.queue, 'get_running_task'):
                running_task = self.queue.get_running_task()
            
            return {
                "status_counts": stats,
                "running_task": running_task,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


def create_agent_loop(parser_prefix: str = None):
    """Factory function to create agent loop."""
    return AgentLoop(parser_prefix)
