"""
Celery worker for Codemail system.
Processes tasks from the queue and executes them with progress tracking.
"""

import os
import sys
import logging
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.getcwd())

from celery_app import celery_app
from task_queue import create_task_queue
from agent_loop import AgentLoop
from email_reporter import create_email_reporter

logger = logging.getLogger("codemail.worker")


@celery_app.task(bind=True, max_retries=3)
def process_task(self, task_id: str):
    """
    Celery task to process a single coding task.
    
    Args:
        task_id: Unique identifier of the task to process
    """
    logger.info(f"Starting Celery task processing for {task_id}")
    
    try:
        # Initialize components
        queue = create_task_queue()
        agent = AgentLoop()
        reporter = create_email_reporter()
        
        # Get task from database
        task = queue.get_task(task_id)
        
        if not task:
            logger.error(f"Task {task_id} not found in database")
            return {"status": "failed", "error": "Task not found"}
        
        logger.info(f"Processing task {task_id}: {task['instructions'][:100]}...")
        
        # Update status to running
        queue.update_task_status(
            task_id=task_id,
            status="running",
            started_at=datetime.now()
        )
        
        # Set initial state in Redis
        if hasattr(queue, 'set_task_state'):
            queue.set_task_state(task_id, {
                "status": "running",
                "message": "Starting execution...",
                "timestamp": datetime.now().isoformat()
            })
        
        # Execute task with progress tracking
        result = agent.execute_task_with_progress(task_id)
        
        # Update task with results
        completed_at = datetime.now()
        queue.update_task_status(
            task_id=task_id,
            status=result["status"],
            completed_at=completed_at,
            output=result.get("output"),
            error=result.get("error")
        )
        
        logger.info(f"Task {task_id} completed with status: {result['status']}")
        
        # Update final state in Redis
        if hasattr(queue, 'set_task_state'):
            queue.set_task_state(task_id, {
                "status": result["status"],
                "message": f"Completed: {result.get('output', '')[:100]}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Send report to sender
        if task.get("sender"):
            reporter.send_task_report(
                recipient=task["sender"],
                task_id=task_id,
                task_data=result
            )
        
        return {
            "status": result["status"],
            "output": result.get("output"),
            "error": result.get("error")
        }
        
    except Exception as exc:
        logger.error(f"Error processing task {task_id}: {exc}")
        
        # Update task status to failed
        queue = create_task_queue()
        queue.update_task_status(
            task_id=task_id,
            status="failed",
            completed_at=datetime.now(),
            error=str(exc)
        )
        
        # Update Redis state for failed task
        if hasattr(queue, 'set_task_state'):
            queue.set_task_state(task_id, {
                "status": "failed",
                "message": f"Error: {str(exc)}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Retry the task (max 3 times)
        raise self.retry(exc=exc, countdown=60)  # Retry after 1 minute


@celery_app.task
def process_queue():
    """
    Process all pending tasks in the queue.
    
    Returns:
        Number of tasks processed
    """
    logger.info("Starting queue processing")
    
    try:
        queue = create_task_queue()
        
        # Get running task count to ensure only one task runs at a time
        running_count = 0
        if hasattr(queue, 'get_running_task'):
            running_task = queue.get_running_task()
            if running_task:
                running_count = 1
        
        processed = 0
        
        while True:
            # Check if we can process more tasks (only one at a time)
            if running_count > 0:
                logger.info("Another task is running, waiting...")
                break
            
            task = queue.get_pending_task()
            
            if not task:
                logger.info("No pending tasks in queue")
                break
            
            # Process the task
            process_task.delay(task["id"])
            processed += 1
            running_count += 1
        
        return {"processed": processed}
        
    except Exception as e:
        logger.error(f"Error processing queue: {e}")
        return {"error": str(e), "processed": 0}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Codemail Celery Worker")
    parser.add_argument("--worker", action="store_true", help="Start Celery worker")
    parser.add_argument("--beat", action="store_true", help="Start Celery beat scheduler")
    
    args = parser.parse_args()
    
    if args.worker:
        logger.info("Starting Celery worker...")
        celery_app.worker_main(["worker", "--loglevel=info"])
    elif args.beat:
        logger.info("Starting Celery beat scheduler...")
        celery_app.worker_main(["beat", "--loglevel=info"])
    else:
        logger.info("Usage: python worker.py [--worker|--beat]")
        logger.info("  --worker   Start Celery worker to process tasks")
        logger.info("  --beat     Start Celery beat scheduler for periodic tasks")
