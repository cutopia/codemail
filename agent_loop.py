"""
Agent loop module for Codemail system.
Orchestrates the execution of tasks using LLM and manages the workflow.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Optional
from email_parser import create_email_parser
from llm_interface import create_llm_interface
from task_queue import create_task_queue
from email_reporter import create_email_reporter

logger = logging.getLogger("codemail.agent_loop")


class AgentLoop:
    """Main agent loop that processes tasks from the queue."""
    
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
            
            # Create task in queue
            task_id = self.queue.create_task(
                project_name=parsed_data["project_name"],
                instructions=parsed_data["instructions"],
                sender=parsed_data.get("sender")
            )
            
            logger.info(f"Task created with ID: {task_id}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return None
    
    def execute_task(self, task_id: str) -> bool:
        """
        Execute a single task from the queue.
        
        Args:
            task_id: Unique identifier of the task to execute
            
        Returns:
            True if execution completed successfully, False otherwise
        """
        try:
            # Get task from queue
            task = self.queue.get_task(task_id)
            
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            logger.info(f"Executing task {task_id}: {task['instructions'][:100]}...")
            
            # Update status to running
            self.queue.update_task_status(
                task_id=task_id,
                status="running",
                started_at=datetime.now()
            )
            
            # Execute with LLM
            result = self.llm.execute_iterative_task(task["instructions"])
            
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
            
            # Send report to sender
            if task.get("sender"):
                self.reporter.send_task_report(
                    recipient=task["sender"],
                    task_id=task_id,
                    task_data=result
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            
            # Update task status to failed
            self.queue.update_task_status(
                task_id=task_id,
                status="failed",
                completed_at=datetime.now(),
                error=str(e)
            )
            
            return False
    
    def process_queue(self, max_tasks: int = None) -> int:
        """
        Process all pending tasks in the queue.
        
        Args:
            max_tasks: Maximum number of tasks to process (None for unlimited)
            
        Returns:
            Number of tasks processed
        """
        from datetime import datetime
        
        processed = 0
        
        while True:
            if max_tasks and processed >= max_tasks:
                break
                
            task = self.queue.get_pending_task()
            
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
                # Process any pending tasks
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
                time.sleep(poll_interval)


def create_agent_loop(parser_prefix: str = None):
    """Factory function to create agent loop."""
    return AgentLoop(parser_prefix)
