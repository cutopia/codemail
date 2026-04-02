"""
Main entry point for Codemail system.
Orchestrates email monitoring and task processing.
"""

import sys
import logging
from email_monitor import create_email_monitor
from agent_loop import create_agent_loop

logger = logging.getLogger("codemail.main")


def main():
    """Main function to start the Codemail system."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    logger.info("Starting Codemail system...")
    
    try:
        # Get codemail prefix from environment
        codemail_prefix = os.getenv("CODEMAIL_PREFIX", "codemail:")
        
        # Create components
        monitor = create_email_monitor()
        agent = create_agent_loop(codemail_prefix)
        
        logger.info(f"Codemail system initialized with prefix: '{codemail_prefix}'")
        logger.info("Codemail system initialized successfully")
        
        def email_callback(email_data):
            """
            Callback function for processing incoming emails.
            
            Args:
                email_data: Dictionary with email content
            """
            try:
                # Process email and create task
                task_id = agent.process_email(email_data)
                
                if task_id:
                    logger.info(f"Email processed successfully. Task ID: {task_id}")
                    
                    # Execute the task immediately (single-task mode)
                    agent.execute_task(task_id)
                    
                elif task_id is None:
                    # Email was parsed but not a valid codemail request
                    logger.info("Email ignored - does not match codemail pattern")
                    
            except Exception as e:
                logger.error(f"Error in email callback: {e}")
        
        # Start monitoring for emails
        monitor.monitor_loop(callback=email_callback, poll_interval=60)
        
    except KeyboardInterrupt:
        logger.info("System stopped by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
