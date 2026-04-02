"""
Database migration script for adding priority column to tasks table.
Run this script to upgrade existing databases to support task priorities.
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()


def add_priority_column():
    """Add priority column to tasks table if it doesn't exist."""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "sqlite:///tasks.db")
    db_path = database_url.replace("sqlite:///", "")
    
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)
    
    print(f"Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if priority column already exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "priority" not in columns:
            print("Adding priority column to tasks table...")
            
            # Add priority column with default value 0
            cursor.execute("""
                ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 0
            """)
            
            # Set default value for existing rows
            cursor.execute("""
                UPDATE tasks SET priority = 0 WHERE priority IS NULL
            """)
            
            # Create index for priority-based queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC)
            """)
            
            conn.commit()
            print("✓ Priority column added successfully!")
        else:
            print("✓ Priority column already exists in database.")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error during migration: {e}")
        raise


if __name__ == "__main__":
    add_priority_column()
