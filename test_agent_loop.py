"""
Test suite for agent loop functionality.
Tests robust error handling, retry logic, and task execution.
"""

import unittest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.getcwd())

from agent_loop import AgentLoop, create_agent_loop


class TestAgentLoop(unittest.TestCase):
    """Test cases for AgentLoop class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set environment variables for testing
        os.environ['CODEMAIL_PREFIX'] = 'test:'
        
        # Mock external dependencies
        self.mock_parser = Mock()
        self.mock_llm = Mock()
        self.mock_queue = Mock()
        self.mock_reporter = Mock()
        
    def test_agent_loop_initialization(self):
        """Test agent loop initialization."""
        with patch('agent_loop.create_email_parser') as mock_parser, \
             patch('agent_loop.create_llm_interface') as mock_llm, \
             patch('agent_loop.create_task_queue') as mock_queue, \
             patch('agent_loop.create_email_reporter') as mock_reporter:
            
            mock_parser.return_value = Mock()
            mock_llm.return_value = Mock()
            mock_queue.return_value = Mock()
            mock_reporter.return_value = Mock()
            
            agent = create_agent_loop()
            
            self.assertIsNotNone(agent)
            self.assertEqual(agent.max_retries, 3)
            self.assertEqual(agent.retry_delay, 60)
    
    def test_process_email_success(self):
        """Test successful email processing."""
        with patch('agent_loop.create_email_parser') as mock_parser, \
             patch('agent_loop.create_llm_interface') as mock_llm, \
             patch('agent_loop.create_task_queue') as mock_queue, \
             patch('agent_loop.create_email_reporter') as mock_reporter:
            
            # Setup mocks
            parser_instance = Mock()
            parser_instance.parse_email.return_value = {
                "project_name": "test-project",
                "instructions": "Test instructions",
                "sender": "test@example.com"
            }
            parser_instance.validate_task.return_value = (True, None)
            
            queue_instance = Mock()
            queue_instance.create_task.return_value = "task-123"
            
            mock_parser.return_value = parser_instance
            mock_queue.return_value = queue_instance
            
            agent = create_agent_loop()
            
            email_data = {
                "subject": "test:[project]",
                "body": "Test instructions",
                "from": "test@example.com"
            }
            
            task_id = agent.process_email(email_data)
            
            self.assertEqual(task_id, "task-123")
            parser_instance.parse_email.assert_called_once_with(email_data)
    
    def test_process_email_invalid(self):
        """Test email processing with invalid data."""
        with patch('agent_loop.create_email_parser') as mock_parser:
            parser_instance = Mock()
            parser_instance.parse_email.return_value = None
            mock_parser.return_value = parser_instance
            
            agent = create_agent_loop()
            
            result = agent.process_email({"subject": "invalid", "body": "", "from": ""})
            
            self.assertIsNone(result)
    
    def test_execute_task_with_progress(self):
        """Test task execution with progress tracking."""
        with patch('agent_loop.create_llm_interface') as mock_llm, \
             patch('agent_loop.create_task_queue') as mock_queue:
            
            queue_instance = Mock()
            queue_instance.get_task.return_value = {
                "id": "task-123",
                "project_name": "test",
                "instructions": "Test instructions"
            }
            queue_instance.update_task_status.return_value = True
            
            llm_instance = Mock()
            llm_instance.execute_iterative_task_with_progress.return_value = {
                "status": "completed",
                "output": "Task completed successfully",
                "error": None
            }
            
            mock_queue.return_value = queue_instance
            mock_llm.return_value = llm_instance
            
            agent = create_agent_loop()
            
            result = agent.execute_task_with_progress("task-123")
            
            self.assertEqual(result["status"], "completed")
            queue_instance.update_task_status.assert_called()
    
    def test_execute_task_retry_logic(self):
        """Test task execution with retry logic."""
        with patch('agent_loop.create_llm_interface') as mock_llm, \
             patch('agent_loop.create_task_queue') as mock_queue:
            
            queue_instance = Mock()
            queue_instance.get_task.return_value = {
                "id": "task-123",
                "project_name": "test",
                "instructions": "Test instructions"
            }
            queue_instance.update_task_status.return_value = True
            
            # Make LLM fail first, then succeed
            llm_instance = Mock()
            llm_instance.execute_iterative_task_with_progress.side_effect = [
                Exception("First attempt failed"),
                Exception("Second attempt failed"),
                {"status": "completed", "output": "Success", "error": None}
            ]
            
            mock_queue.return_value = queue_instance
            mock_llm.return_value = llm_instance
            
            agent = create_agent_loop()
            agent.max_retries = 2  # Test with 2 retries
            
            result = agent.execute_task("task-123")
            
            self.assertTrue(result)
    
    def test_execute_task_max_retries_exceeded(self):
        """Test task execution when max retries are exceeded."""
        with patch('agent_loop.create_llm_interface') as mock_llm, \
             patch('agent_loop.create_task_queue') as mock_queue:
            
            queue_instance = Mock()
            queue_instance.get_task.return_value = {
                "id": "task-123",
                "project_name": "test",
                "instructions": "Test instructions"
            }
            queue_instance.update_task_status.return_value = True
            
            # Make LLM always fail
            llm_instance = Mock()
            llm_instance.execute_iterative_task_with_progress.side_effect = Exception("Always fails")
            
            mock_queue.return_value = queue_instance
            mock_llm.return_value = llm_instance
            
            agent = create_agent_loop()
            agent.max_retries = 1  # Only 1 retry allowed
            
            result = agent.execute_task("task-123")
            
            self.assertFalse(result)
    
    def test_progress_callback(self):
        """Test progress callback function."""
        with patch('agent_loop.create_task_queue') as mock_queue:
            queue_instance = Mock()
            queue_instance.update_task_progress.return_value = True
            mock_queue.return_value = queue_instance
            
            agent = create_agent_loop()
            
            result = agent._progress_callback("task-123", 5, 10, "Processing...")
            
            self.assertTrue(result)
            queue_instance.update_task_progress.assert_called_once_with(
                "task-123", 5, 10, "Processing..."
            )
    
    def test_process_queue(self):
        """Test queue processing."""
        with patch('agent_loop.create_llm_interface') as mock_llm, \
             patch('agent_loop.create_task_queue') as mock_queue:
            
            queue_instance = Mock()
            # Return None after first call to simulate emptying the queue
            queue_instance.get_pending_task.side_effect = [
                {"id": "task-1", "project_name": "test", "instructions": "Test", "priority": 0},
                None  # No more tasks
            ]
            mock_queue.return_value = queue_instance
            
            llm_instance = Mock()
            llm_instance.execute_iterative_task_with_progress.return_value = {
                "status": "completed",
                "output": "Success",
                "error": None
            }
            
            def execute_task_side_effect(task_id):
                return True  # Always succeed
            
            agent = create_agent_loop()
            agent.execute_task = Mock(side_effect=execute_task_side_effect)
            
            processed = agent.process_queue(max_tasks=5)
            
            self.assertEqual(processed, 1)  # Only one task was in queue
    
    def test_get_queue_status(self):
        """Test queue status retrieval."""
        with patch('agent_loop.create_task_queue') as mock_queue:
            queue_instance = Mock()
            queue_instance.get_queue_stats.return_value = {
                "pending": 5,
                "running": 2,
                "completed": 10,
                "failed": 1
            }
            mock_queue.return_value = queue_instance
            
            agent = create_agent_loop()
            
            status = agent.get_queue_status()
            
            self.assertIn("status_counts", status)
            self.assertEqual(status["status_counts"]["pending"], 5)


class TestAgentLoopIntegration(unittest.TestCase):
    """Integration tests for agent loop with real dependencies."""
    
    def setUp(self):
        """Set up test fixtures."""
        os.environ['DATABASE_URL'] = 'sqlite:///test_tasks.db'
        
    def tearDown(self):
        """Clean up test database."""
        import os
        if os.path.exists('test_tasks.db'):
            os.remove('test_tasks.db')
    
    def test_full_task_execution(self):
        """Test complete task execution flow."""
        # Clean up any existing test database
        import os
        if os.path.exists('test_tasks.db'):
            os.remove('test_tasks.db')
        
        agent = create_agent_loop()
        
        # Create a simple task
        task_id = agent.queue.create_task(
            project_name="test-project",
            instructions="Write a function that returns 'Hello, World!'",
            priority=1
        )
        
        self.assertIsNotNone(task_id)
        
        # Get the task
        task = agent.queue.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["project_name"], "test-project")
        self.assertIn("priority", task)  # Priority field should exist
    
    def test_priority_queue(self):
        """Test priority-based queue ordering."""
        # Clean up any existing test database
        import os
        if os.path.exists('test_tasks.db'):
            os.remove('test_tasks.db')
        
        agent = create_agent_loop()
        
        # Create tasks with different priorities
        task_low = agent.queue.create_task(
            project_name="low-priority",
            instructions="Low priority task",
            priority=0
        )
        
        task_high = agent.queue.create_task(
            project_name="high-priority",
            instructions="High priority task",
            priority=10
        )
        
        # Get pending tasks - should get high priority first
        first_task = agent.queue.get_pending_task()
        self.assertEqual(first_task["priority"], 10)  # Check priority, not ID
        
        # Verify both tasks exist in database
        all_tasks = agent.queue.get_all_tasks(limit=2)
        task_ids = [t["id"] for t in all_tasks]
        
        self.assertIn(task_low, task_ids)
        self.assertIn(task_high, task_ids)


if __name__ == '__main__':
    unittest.main()
