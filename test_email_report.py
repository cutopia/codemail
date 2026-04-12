#!/usr/bin/env python3
"""
Test script for Codemail email reporting.
Tests the email reporter with various scenarios.
"""

import os
import sys
import logging

# Add current directory to path
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test_email_report")


def test_email_reporter():
    """Test the email reporter with a simple message."""
    logger.info("Testing Codemail Email Reporter")
    
    try:
        from email_reporter import create_email_reporter
        
        # Create reporter
        reporter = create_email_reporter()
        
        if not reporter:
            logger.error("Failed to create email reporter")
            return False
        
        logger.info("Email reporter created successfully")
        
        # Test with a simple task result
        test_task_id = "test-12345"
        test_result = {
            "status": "completed",
            "output": "Task completed successfully!",
            "error": None,
            "iterations": 2,
            "step_summaries": [
                {
                    "step": 1,
                    "description": "Initial execution",
                    "summary": "Executed initial task with 3 bash commands"
                },
                {
                    "step": 2,
                    "description": "Refinement",
                    "summary": "Refined output based on feedback"
                }
            ],
            "bash_results": [
                {
                    "command": "echo 'Hello, World!'",
                    "result": {
                        "stdout": "Hello, World!",
                        "stderr": "",
                        "returncode": 0
                    }
                },
                {
                    "command": "ls -la",
                    "result": {
                        "stdout": "total 8\ndrwxr-xr-x 2 user user 4096 Apr 11 22:00 .",
                        "stderr": "",
                        "returncode": 0
                    }
                }
            ]
        }
        
        # Get recipient from environment or use default
        recipient = os.getenv("EMAIL_ADDRESS", "test@example.com")
        
        logger.info(f"Testing email report to {recipient}")
        
        # Send test report
        success = reporter.send_task_report(
            recipient=recipient,
            task_id=test_task_id,
            task_data=test_result
        )
        
        if success:
            logger.info("✅ Email report sent successfully!")
            return True
        else:
            logger.error("❌ Failed to send email report")
            return False
            
    except Exception as e:
        logger.error(f"Error testing email reporter: {e}", exc_info=True)
        return False


def test_whitelist_check():
    """Test whitelist checking functionality."""
    logger.info("Testing Whitelist Functionality")
    
    try:
        from whitelist import get_email_whitelist
        
        whitelist = get_email_whitelist()
        
        if not whitelist:
            logger.error("Failed to create whitelist")
            return False
        
        # Test with the configured email address
        test_email = os.getenv("EMAIL_ADDRESS", "test@example.com")
        
        is_whitelisted = whitelist.is_recipient_whitelisted(test_email)
        
        logger.info(f"Email '{test_email}' whitelist status: {is_whitelisted}")
        
        if is_whitelisted:
            logger.info("✅ Email is whitelisted")
            return True
        else:
            logger.warning(f"❌ Email '{test_email}' is not whitelisted")
            
            # Check what's in the whitelist
            logger.info(f"Whitelist contains: {whitelist.allowed_recipients}")
            
            return False
            
    except Exception as e:
        logger.error(f"Error testing whitelist: {e}", exc_info=True)
        return False


def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("Codemail Email Reporting Test Suite")
    logger.info("=" * 60)
    
    # Check environment variables
    required_vars = ["EMAIL_ADDRESS", "SMTP_HOST"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file before running tests")
        return False
    
    logger.info("Environment variables OK")
    
    # Run tests
    results = {}
    
    # Test 1: Whitelist check
    results["whitelist"] = test_whitelist_check()
    
    # Test 2: Email reporter
    results["reporter"] = test_email_reporter()
    
    # Summary
    logger.info("=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("All tests passed! ✅")
        return True
    else:
        logger.error("Some tests failed. ❌")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
