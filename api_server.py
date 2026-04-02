"""
API server for Codemail system.
Provides REST endpoints for task queue status and management.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from task_queue import create_task_queue

app = FastAPI(
    title="Codemail API",
    description="REST API for Codemail task queue management",
    version="1.0.0"
)

# Create task queue instance
task_queue = create_task_queue()


class TaskResponse(BaseModel):
    """Task response model."""
    id: str
    project_name: str
    instructions: str
    status: str
    sender: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None


class TaskCreateRequest(BaseModel):
    """Task creation request model."""
    project_name: str
    instructions: str
    sender: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "Codemail API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(limit: int = 10, status: Optional[str] = None):
    """
    Get all tasks with optional filtering.
    
    Args:
        limit: Maximum number of tasks to return
        status: Filter by task status (pending, running, completed, failed)
    """
    try:
        if status:
            # Note: This would require SQL modification for filtering
            all_tasks = task_queue.get_all_tasks(limit)
            filtered_tasks = [t for t in all_tasks if t['status'] == status]
            return filtered_tasks
        else:
            return task_queue.get_all_tasks(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task by ID."""
    try:
        task = task_queue.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreateRequest):
    """Create a new task."""
    try:
        task_id = task_queue.create_task(
            project_name=task.project_name,
            instructions=task.instructions,
            sender=task.sender
        )
        
        # Get the created task
        created_task = task_queue.get_task(task_id)
        return created_task
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    """
    Update task status.
    
    Valid statuses: pending, running, completed, failed
    """
    try:
        valid_statuses = ['pending', 'running', 'completed', 'failed']
        
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        task = task_queue.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Update status
        updated = task_queue.update_task_status(
            task_id=task_id,
            status=status,
            completed_at=datetime.now() if status in ['completed', 'failed'] else None
        )
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update task status")
        
        return {"message": f"Task {task_id} status updated to {status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    try:
        task = task_queue.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        deleted = task_queue.delete_task(task_id)
        
        if deleted:
            return {"message": f"Task {task_id} deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete task")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/status")
async def get_queue_status():
    """Get queue statistics."""
    try:
        all_tasks = task_queue.get_all_tasks()
        
        status_counts = {
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0
        }
        
        for task in all_tasks:
            status = task['status']
            if status in status_counts:
                status_counts[status] += 1
        
        return {
            "total_tasks": len(all_tasks),
            "pending": status_counts['pending'],
            "running": status_counts['running'],
            "completed": status_counts['completed'],
            "failed": status_counts['failed']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Codemail API server...")
    print("API available at http://localhost:8000")
    print("Docs at http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
