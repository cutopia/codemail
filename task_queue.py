"""
Task queue module for Codemail system.
Manages task storage and basic queuing functionality.
"""

import sqlite3
import uuid
import os
from datetime import datetime
import logging
from typing import Dict, List, Optional
from config import database_config

logger = logging.getLogger("codemail.task_queue")


class TaskQueue:
    """SQLite-based task queue for managing coding tasks."""
    
    def __init__(self):
        self.database_url = database_config.database_url
        self._create_tables()
        
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
                    error TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Task queue tables initialized")
            
        except Exception as e:
            logger.error(f"Error creating task tables: {e}")
            raise
    
    def create_task(self, project_name: str, instructions: str, sender: str = None) -> str:
        """
        Create a new task in the queue.
        
        Args:
            project_name: Name of the project to work on
            instructions: Task instructions from email
            sender: Email sender address
            
        Returns:
            Unique task ID
        """
        try:
            task_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tasks (id, project_name, instructions, status, sender, created_at)
                VALUES (?, ?, ?, 'pending', ?, ?)
            ''', (task_id, project_name, instructions, sender, created_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created task {task_id} for project '{project_name}'")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise
    
    def get_pending_task(self) -> Optional[Dict]:
        """
        Get the next pending task from the queue.
        
        Returns:
            Task dictionary or None if no pending tasks
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, project_name, instructions, sender, created_at
                FROM tasks
                WHERE status = 'pending'
                ORDER BY created_at ASC
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
                    "created_at": row[4]
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
                       created_at, started_at, completed_at, output, error
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
                    "error": row[9]
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
            
            logger.info(f"Deleted task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False


def create_task_queue():
    """Factory function to create task queue."""
    return TaskQueue()
