"""
Agent loop module for Codemail system.
Orchestrates the execution of tasks using LLM and manages the workflow with robust error handling.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List, Any
from email_parser import create_email_parser
from llm_interface import create_llm_interface
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
        self.queue = create_task_queue()
        self.reporter = create_email_reporter()
        
        # Configuration
        self.max_retries = int(os.getenv("AGENT_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("AGENT_RETRY_DELAY", "60"))  # seconds
        self.task_timeout = int(os.getenv("TASK_TIMEOUT", "3600"))  # 1 hour default
        
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
            
            logger.info(f"Executing task {task_id}: {task['instructions'][:100]}...")
            
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
            
            # Execute with LLM and progress tracking
            result = self.llm.execute_iterative_task_with_progress(
                task["instructions"],
                task_id=task_id,
                progress_callback=self._progress_callback
            )
            
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
                
                logger.info(f"Executing task {task_id} (attempt {attempt + 1}/{self.max_retries + 1}): {task['instructions'][:100]}...")
                
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
                
                # Execute with LLM and progress tracking
                result = self.llm.execute_iterative_task_with_progress(
                    task["instructions"],
                    task_id=task_id,
                    progress_callback=self._progress_callback
                )
                
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
