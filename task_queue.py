"""
Task queue module for Codemail system.
Manages task storage and basic queuing functionality with Celery integration.
"""

import sqlite3
import uuid
import os
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
from config import database_config, redis_config

logger = logging.getLogger("codemail.task_queue")


class TaskQueue:
    """SQLite-based task queue for managing coding tasks with Redis state tracking."""
    
    def __init__(self):
        self.database_url = database_config.database_url
        self.redis_url = redis_config.redis_url
        self._create_tables()
        self._redis_client = None
        
    @property
    def redis(self):
        """Get or create Redis client."""
        if self._redis_client is None:
            try:
                import redis as redis_module
                # Parse Redis URL to extract connection parameters
                if self.redis_url.startswith("redis://"):
                    parsed = self.redis_url.replace("redis://", "")
                    host_port = parsed.split("/")[0] if "/" in parsed else parsed
                    host, port = host_port.split(":") if ":" in host_port else ("localhost", 6379)
                    db = int(parsed.split("/")[-1]) if "/" in parsed and parsed.split("/")[-1].isdigit() else 0
                    
                    self._redis_client = redis_module.Redis(
                        host=host,
                        port=int(port),
                        db=db,
                        decode_responses=True
                    )
                else:
                    # Fallback to default connection
                    self._redis_client = redis_module.Redis(decode_responses=True)
                    
                logger.info(f"Redis connected: {self.redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using SQLite only.")
                self._redis_client = None
        
        return self._redis_client
        
    def _get_connection(self):
        """Get database connection."""
        # Handle both absolute paths and simple filenames
        db_path = self.database_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            # If relative path, use current directory
            db_path = os.path.join(os.getcwd(), db_path)
        
        return sqlite3.connect(db_path)
    
    def _create_tables(self):
        """Create task table if it doesn't exist."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    sender TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    output TEXT,
                    error TEXT,
                    priority INTEGER DEFAULT 0
                )
            ''')
            
            # Create index for priority-based queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Task queue tables initialized")
            
        except Exception as e:
            logger.error(f"Error creating task tables: {e}")
            raise
    
    def create_task(self, project_name: str, instructions: str, sender: str = None,
                   priority: int = 0) -> str:
        """
        Create a new task in the queue.
        
        Args:
            project_name: Name of the project to work on
            instructions: Task instructions from email
            sender: Email sender address
            priority: Task priority (higher = more urgent, default 0)
            
        Returns:
            Unique task ID
        """
        try:
            task_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tasks (id, project_name, instructions, status, sender, created_at, priority)
                VALUES (?, ?, ?, 'pending', ?, ?, ?)
            ''', (task_id, project_name, instructions, sender, created_at, priority))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created task {task_id} for project '{project_name}' with priority {priority}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise
    
    def get_pending_task(self, priority_only: bool = False) -> Optional[Dict]:
        """
        Get the next pending task from the queue.
        
        Args:
            priority_only: If True, only return high-priority tasks (priority > 0)
            
        Returns:
            Task dictionary or None if no pending tasks
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build query with optional priority filter
            if priority_only:
                cursor.execute('''
                    SELECT id, project_name, instructions, sender, created_at, priority
                    FROM tasks
                    WHERE status = 'pending' AND priority > 0
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                ''')
            else:
                cursor.execute('''
                    SELECT id, project_name, instructions, sender, created_at, priority
                    FROM tasks
                    WHERE status = 'pending'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "project_name": row[1],
                    "instructions": row[2],
                    "sender": row[3],
                    "created_at": row[4],
                    "priority": row[5] if len(row) > 5 else 0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting pending task: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: str, 
                          started_at: datetime = None, completed_at: datetime = None,
                          output: str = None, error: str = None) -> bool:
        """
        Update task status and results.
        
        Args:
            task_id: Unique task identifier
            status: New status (running, completed, failed)
            started_at: When task started execution
            completed_at: When task finished execution
            output: Task output/results
            error: Error message if task failed
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build update query dynamically based on provided parameters
            updates = []
            values = []
            
            if status:
                updates.append("status = ?")
                values.append(status)
                
            if started_at:
                updates.append("started_at = ?")
                values.append(started_at.isoformat())
                
            if completed_at:
                updates.append("completed_at = ?")
                values.append(completed_at.isoformat())
                
            if output is not None:
                updates.append("output = ?")
                values.append(output)
                
            if error is not None:
                updates.append("error = ?")
                values.append(error)
            
            if not updates:
                logger.warning("No fields to update for task")
                return False
            
            values.append(task_id)
            
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            logger.info(f"Updated task {task_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Get a specific task by ID.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Task dictionary or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, project_name, instructions, status, sender,
                       created_at, started_at, completed_at, output, error, priority
                FROM tasks WHERE id = ?
            ''', (task_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "project_name": row[1],
                    "instructions": row[2],
                    "status": row[3],
                    "sender": row[4],
                    "created_at": row[5],
                    "started_at": row[6],
                    "completed_at": row[7],
                    "output": row[8],
                    "error": row[9],
                    "priority": row[10] if len(row) > 10 else 0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    def get_all_tasks(self, limit: int = 10) -> List[Dict]:
        """
        Get all tasks (latest first).
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of task dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, project_name, instructions, status, sender,
                       created_at, started_at, completed_at, output, error
                FROM tasks
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                "id": row[0],
                "project_name": row[1],
                "instructions": row[2],
                "status": row[3],
                "sender": row[4],
                "created_at": row[5],
                "started_at": row[6],
                "completed_at": row[7],
                "output": row[8],
                "error": row[9]
            } for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting all tasks: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the queue.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            conn.close()
            
            # Clean up Redis state if available
            if self.redis:
                try:
                    self.redis.delete(f"task:{task_id}:progress")
                    self.redis.delete(f"task:{task_id}:state")
                except Exception as e:
                    logger.debug(f"Failed to clean up Redis for task {task_id} (Redis may not be available): {e}")
            
            logger.info(f"Deleted task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    # ==================== Enhanced State Management Methods ====================
    
    def set_task_state(self, task_id: str, state: Dict[str, Any]) -> bool:
        """
        Set task state in Redis for real-time tracking.
        
        Args:
            task_id: Unique task identifier
            state: Dictionary of state information
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            key = f"task:{task_id}:state"
            self.redis.setex(key, 3600, json.dumps(state))  # 1 hour TTL
            logger.debug(f"Set state for task {task_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to set task state (Redis may not be available): {e}")
            return False
    
    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task state from Redis.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            State dictionary or None if not found
        """
        if not self.redis:
            return None
        
        try:
            key = f"task:{task_id}:state"
            data = self.redis.get(key)
            
            if data:
                return json.loads(data)
            
            return None
        except Exception as e:
            logger.warning(f"Failed to get task state (Redis may not be available): {e}")
            return None
    
    def update_task_progress(self, task_id: str, current_step: int, total_steps: int,
                            message: str = "", status: str = "running") -> bool:
        """
        Update task progress for real-time tracking.
        
        Args:
            task_id: Unique task identifier
            current_step: Current step number
            total_steps: Total number of steps
            message: Progress message
            status: Current status
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            progress_data = {
                "current_step": current_step,
                "total_steps": total_steps,
                "message": message,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "percentage": (current_step / total_steps * 100) if total_steps > 0 else 0
            }
            
            key = f"task:{task_id}:progress"
            self.redis.setex(key, 3600, json.dumps(progress_data))  # 1 hour TTL
            
            logger.debug(f"Updated progress for task {task_id}: {current_step}/{total_steps}")
            return True
        except Exception as e:
            logger.warning(f"Failed to update task progress (Redis may not be available): {e}")
            return False
    
    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task progress from Redis.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Progress dictionary or None if not found
        """
        if not self.redis:
            return None
        
        try:
            key = f"task:{task_id}:progress"
            data = self.redis.get(key)
            
            if data:
                return json.loads(data)
            
            return None
        except Exception as e:
            logger.warning(f"Failed to get task progress (Redis may not be available): {e}")
            return None
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        Get queue statistics including pending, running, completed, and failed counts.
        
        Returns:
            Dictionary with status counts
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get counts for each status
            cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
            rows = cursor.fetchall()
            conn.close()
            
            stats = {
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "stopped": 0
            }
            
            for row in rows:
                status, count = row
                if status in stats:
                    stats[status] = count
            
            return stats
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {"pending": 0, "running": 0, "completed": 0, "failed": 0, "stopped": 0}
    
    def stop_task(self, task_id: str) -> bool:
        """
        Mark a task as stopped.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE tasks SET status = 'stopped', completed_at = ? WHERE id = ?
            ''', (datetime.now().isoformat(), task_id))
            
            conn.commit()
            conn.close()
            
            # Update Redis state
            if self.redis:
                try:
                    self.set_task_state(task_id, {"status": "stopped", "message": "Task was stopped by user"})
                except Exception as e:
                    logger.warning(f"Failed to update Redis state for stopped task {task_id}: {e}")
            
            logger.info(f"Stopped task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping task {task_id}: {e}")
            return False
    
    def get_pending_tasks_count(self) -> int:
        """
        Get the number of pending tasks in the queue.
        
        Returns:
            Number of pending tasks
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"Error getting pending task count: {e}")
            return 0
    
    def get_running_task(self) -> Optional[Dict]:
        """
        Get the currently running task (if any).
        
        Returns:
            Task dictionary or None if no running task
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, project_name, instructions, status, sender,
                       created_at, started_at, completed_at, output, error
                FROM tasks WHERE status = 'running'
                ORDER BY started_at DESC LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "project_name": row[1],
                    "instructions": row[2],
                    "status": row[3],
                    "sender": row[4],
                    "created_at": row[5],
                    "started_at": row[6],
                    "completed_at": row[7],
                    "output": row[8],
                    "error": row[9]
                }
            
            return None
        except Exception as e:
            logger.error(f"Error getting running task: {e}")
            return None


def create_task_queue():
    """Factory function to create task queue."""
    return TaskQueue()


def create_task_queue():
    """Factory function to create task queue."""
    return TaskQueue()
