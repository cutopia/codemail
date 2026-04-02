# Phase 2: Task Queue Foundation

## Overview

Phase 2 implements an enhanced task queue system with Celery and Redis integration for distributed task processing, real-time progress tracking, and better state management.

## ✅ Completed Features

### 1. Enhanced Task Queue (`task_queue.py`)

- **SQLite-based storage** - Persistent task history
- **Redis state tracking** - Real-time task state and progress monitoring
- **Task status management** - Supports: pending, running, completed, failed, stopped
- **Progress tracking** - Track execution progress with step counts and messages
- **Queue statistics** - Get counts of tasks by status

### 2. Celery Integration (`celery_app.py`)

- **Distributed task processing** - Process tasks across multiple workers
- **Task queue management** - Handle concurrent task execution
- **Retry mechanism** - Automatic retry on failure with exponential backoff
- **Worker and beat scheduler** - Support for both worker and scheduler modes

### 3. Agent Loop Enhancements (`agent_loop.py`)

- **Progress callbacks** - Real-time progress updates during task execution
- **State tracking** - Update Redis state throughout task lifecycle
- **Enhanced error handling** - Better error reporting and recovery

### 4. LLM Interface Updates (`llm_interface.py`)

- **Progress callback support** - Track iterative refinement steps
- **Legacy compatibility** - Maintain backward compatibility with existing code

### 5. API Server Extensions (`api_server.py`)

- **Task progress endpoint** - `/tasks/{task_id}/progress`
- **Task stop endpoint** - `/tasks/{task_id}/stop`
- **Enhanced queue status** - Include Redis availability and detailed stats
- **Real-time monitoring** - Track task execution in real-time

### 6. Celery Worker (`worker.py`)

- **Task processing** - Process tasks from the queue
- **Progress tracking** - Update progress throughout execution
- **Error handling** - Retry failed tasks with backoff
- **Command-line interface** - Start worker or beat scheduler

## 📊 Task Status Flow

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│ pending │────▶│ running │────▶│ completed│
└─────────┘     └─────────┘     └──────────┘
      │              │              ▲
      │              ▼              │
      │           ┌─────────┐       │
      └──────────▶│  failed │───────┘
                  └─────────┘
                      │
                      ▼
                 ┌─────────┐
                 │ stopped │
                 └─────────┘
```

## 🚀 Usage

### Starting the System

#### Option 1: Direct Execution (Single Task Mode)

```bash
source venv/bin/activate
python main.py
```

This mode processes one task at a time and is suitable for development/testing.

#### Option 2: Celery Worker (Distributed Mode)

Start the Celery worker to process tasks from the queue:

```bash
source venv/bin/activate

# Start Celery worker
celery -A celery_app worker --loglevel=info

# Or use the provided script
python worker.py --worker
```

#### Option 3: Celery Beat Scheduler (Periodic Tasks)

Start the beat scheduler for periodic task processing:

```bash
source venv/bin/activate

# Start Celery beat scheduler
celery -A celery_app beat --loglevel=info

# Or use the provided script
python worker.py --beat
```

### API Endpoints

#### Get Queue Status

```bash
curl http://localhost:8000/queue/status
```

Response:
```json
{
  "total_tasks": 15,
  "pending": 3,
  "running": 1,
  "completed": 10,
  "failed": 1,
  "stopped": 0,
  "redis_available": true
}
```

#### Get Task Progress

```bash
curl http://localhost:8000/tasks/{task_id}/progress
```

Response:
```json
{
  "task": {
    "id": "abc-123",
    "project_name": "my-project",
    "instructions": "Fix the login bug",
    "status": "running",
    "created_at": "2024-01-01T12:00:00"
  },
  "progress": {
    "current_step": 3,
    "total_steps": 5,
    "message": "Refinement iteration 3/5",
    "percentage": 60.0
  }
}
```

#### Stop a Task

```bash
curl -X PATCH http://localhost:8000/tasks/{task_id}/stop
```

Response:
```json
{
  "message": "Task abc-123 has been stopped"
}
```

## 🔄 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Redis Configuration (required for Phase 2)
REDIS_URL=redis://localhost:6379/0

# Task Queue Settings
TASK_TIME_LIMIT=3600        # Maximum task execution time in seconds
WORKER_PREFETCH_MULTIPLIER=1  # Process one task at a time
```

### Redis Setup

#### Option 1: Install Redis Locally

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS with Homebrew
brew install redis
brew services start redis
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

#### Option 2: Use Docker

```bash
docker run -d --name codemail-redis -p 6379:6379 redis:alpine
```

#### Option 3: SQLite Only (No Redis)

If Redis is not available, the system will fall back to SQLite-only mode with limited functionality.

## 🧪 Testing

### Run Unit Tests

```bash
source venv/bin/activate
python test_system.py
```

### Test Celery Integration

1. Start Redis server:
```bash
redis-server
```

2. Start Celery worker in one terminal:
```bash
celery -A celery_app worker --loglevel=info
```

3. Create a task via API:
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_name": "test", "instructions": "Write a hello world function"}'
```

4. Monitor the worker terminal for task processing

### Test Progress Tracking

1. Start the API server:
```bash
python api_server.py
```

2. Create a task and monitor its progress:
```bash
# Create task
TASK_ID=$(curl -s -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_name": "test", "instructions": "Write a test function"}' | jq -r '.id')

# Monitor progress
curl http://localhost:8000/tasks/$TASK_ID/progress
```

## 📁 New Files

- `celery_app.py` - Celery application configuration
- `worker.py` - Celery worker for task processing

## 🔧 Modified Files

- `task_queue.py` - Enhanced with Redis state tracking and progress management
- `agent_loop.py` - Added progress callback support and enhanced execution
- `llm_interface.py` - Added progress callback parameter to iterative execution
- `api_server.py` - Added new endpoints for task progress and stopping
- `requirements.txt` - Updated dependencies

## 🎯 Next Steps (Phase 3)

- [ ] Bash command execution capability
- [ ] Project context awareness
- [ ] Concurrent task processing (multiple workers)
- [ ] Task priority queue
- [ ] Task history analytics

## 🔍 Troubleshooting

### Redis Connection Issues

If you see "Failed to connect to Redis" warnings, the system will fall back to SQLite mode. To fix:

1. Ensure Redis is running: `redis-cli ping`
2. Check Redis URL in `.env`: `REDIS_URL=redis://localhost:6379/0`
3. Verify network connectivity to Redis server

### Celery Worker Not Processing Tasks

1. Ensure Redis is running and accessible
2. Start the worker: `celery -A celery_app worker --loglevel=info`
3. Check worker logs for errors
4. Verify task was created in database

### Task Stuck in Running Status

1. Check if the worker process is still running
2. Manually update task status in database:
```sql
UPDATE tasks SET status = 'failed' WHERE id = '{task_id}' AND status = 'running';
```
3. Restart the worker

## 📚 References

- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/documentation)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
