"""
Workflow module for Codemail system.
Provides the complete end-to-end workflow from email to report.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from email_monitor import create_email_monitor
from email_parser import create_email_parser
from llm_interface import create_llm_interface
from task_queue import create_task_queue
from email_reporter import create_email_reporter

logger = logging.getLogger("codemail.workflow")


class CodemailWorkflow:
    """Complete workflow for processing emails and executing tasks."""
    
    def __init__(self):
        self.parser = create_email_parser()
        self.llm = create_llm_interface()
        self.queue = create_task_queue()
        self.reporter = create_email_reporter()
        
    def process_single_email(self, email_data: Dict) -> Optional[str]:
        """
        Process a single email and return task ID.
        
        Args:
            email_data: Dictionary with 'subject', 'body', 'from' keys
            
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            logger.info("Starting email processing workflow...")
            
            # Step 1: Parse email content
            parsed_data = self.parser.parse_email(email_data)
            
            if not parsed_data:
                logger.error("Failed to parse email")
                return None
            
            logger.info(f"Parsed email - Project: {parsed_data['project_name']}")
            
            # Step 2: Validate task data
            is_valid, error_msg = self.parser.validate_task(parsed_data)
            
            if not is_valid:
                logger.error(f"Invalid task: {error_msg}")
                return None
            
            # Step 3: Create task in queue
            task_id = self.queue.create_task(
                project_name=parsed_data["project_name"],
                instructions=parsed_data["instructions"],
                sender=parsed_data.get("sender")
            )
            
            logger.info(f"Task created with ID: {task_id}")
            
            # Step 4: Execute the task
            success = self.execute_task(task_id)
            
            if success:
                return task_id
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error in email processing workflow: {e}")
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
                logger.info(f"Report sent to {task['sender']}")
            
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
    
    def run_monitoring(self, poll_interval: int = 60):
        """
        Run the complete monitoring workflow.
        
        Args:
            poll_interval: Seconds between email checks
        """
        monitor = create_email_monitor()
        
        def email_callback(email_data):
            """Callback function for processing incoming emails."""
            try:
                # Process email and create task
                task_id = self.process_single_email(email_data)
                
                if task_id:
                    logger.info(f"Email processed successfully. Task ID: {task_id}")
                else:
                    logger.warning("Failed to process email")
                    
            except Exception as e:
                logger.error(f"Error in email callback: {e}")
        
        # Start monitoring for emails
        monitor.monitor_loop(callback=email_callback, poll_interval=poll_interval)


def create_workflow():
    """Factory function to create Codemail workflow."""
    return CodemailWorkflow()


if __name__ == "__main__":
    import sys
    
    logger.info("Codemail Workflow System")
    logger.info("=" * 50)
    
    try:
        # Test the workflow with sample data
        workflow = create_workflow()
        
        # Sample email for testing
        test_email = {
            "subject": "[test-project] Create a simple Python function",
            "body": """Project: test-project

Please implement a Python function that calculates the factorial of a number.
The function should handle edge cases like negative numbers and zero.""",
            "from": "user@example.com"
        }
        
        logger.info("Testing workflow with sample email...")
        task_id = workflow.process_single_email(test_email)
        
        if task_id:
            logger.info(f"Workflow test completed. Task ID: {task_id}")
        else:
            logger.error("Workflow test failed")
            
    except KeyboardInterrupt:
        logger.info("System stopped by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
