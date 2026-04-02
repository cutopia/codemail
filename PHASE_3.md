# Phase 3: Robust Agentic Loop Implementation

## Overview

Phase 3 focuses on creating a robust, production-ready agentic loop with enhanced error handling, retry logic, priority queuing, and comprehensive monitoring capabilities.

## ✅ Completed Features

### 1. Enhanced Agent Loop (`agent_loop.py`)

#### Retry Logic
- **Configurable retries**: Set `AGENT_MAX_RETRIES` environment variable (default: 3)
- **Configurable delay**: Set `AGENT_RETRY_DELAY` environment variable (default: 60 seconds)
- **Automatic retry on failure**: Tasks are automatically retried up to the configured limit
- **Progress tracking during retries**: Each attempt is tracked in Redis state

#### Priority Queue Support
- **Priority field added to tasks**: Higher priority tasks are processed first
- **Configurable via `create_task()`**: Pass `priority` parameter when creating tasks
- **Smart ordering**: Tasks ordered by priority (descending) then creation time (ascending)

#### Timeout Protection
- **Task timeout**: Set `TASK_TIMEOUT` environment variable (default: 3600 seconds = 1 hour)
- **Automatic timeout detection**: Long-running tasks are marked as failed
- **Configurable per task**: Can be extended for complex operations

#### Improved Error Handling
- **Comprehensive error logging**: All errors are logged with context
- **Graceful degradation**: System continues operating even if individual tasks fail
- **Detailed error messages**: Errors include attempt count and last failure reason

### 2. Priority Queue Implementation (`task_queue.py`)

#### Database Schema Changes
```sql
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
    priority INTEGER DEFAULT 0  -- NEW FIELD
)
```

#### Index for Priority Queries
```sql
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC)
```

#### New Methods
- `create_task(project_name, instructions, sender=None, priority=0)`: Create task with priority
- `get_pending_task(priority_only=False)`: Get next pending task, optionally filtered by priority

### 3. Monitoring System (`monitoring.py`)

#### System Status
```python
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00",
    "uptime_seconds": 3600,
    "version": "1.0.0-alpha",
    "queue_stats": {...},
    "components": {
        "email_monitor": {"status": "configured"},
        "llm_interface": {"status": "connected"},
        "task_queue": {"status": "connected"}
    }
}
```

#### Health Check Endpoints
- `/health/status`: Comprehensive system health status
- `/health/ready`: Readiness probe for Kubernetes-style deployment

#### Metrics Collection
```python
{
    "total": 100,
    "completed": 85,
    "failed": 10,
    "running": 5,
    "success_rate": 85.0
}
```

### 4. API Server Enhancements (`api_server.py`)

#### New Endpoints

##### Health Status
```bash
GET /health/status
```
Returns comprehensive system health including all components.

##### Readiness Probe
```bash
GET /health/ready
```
Returns readiness status for Kubernetes-style deployment.

##### Metrics
```bash
GET /metrics
```
Returns system metrics and statistics.

### 5. Configuration Options

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MAX_RETRIES` | 3 | Maximum retry attempts per task |
| `AGENT_RETRY_DELAY` | 60 | Seconds between retry attempts |
| `TASK_TIMEOUT` | 3600 | Maximum task execution time in seconds |
| `PRIORITY_DEFAULT` | 0 | Default priority for new tasks |

## 🚀 Usage

### Starting the System

#### Option 1: Direct Execution (Single Task Mode)

```bash
source venv/bin/activate
python main.py
```

This mode processes one task at a time with retry logic and timeout protection.

#### Option 2: Celery Worker (Distributed Mode)

Start the Celery worker to process tasks from the queue:

```bash
source venv/bin/activate

# Start Celery worker
celery -A celery_app worker --loglevel=info

# Or use the provided script
python worker.py --worker
```

### Creating Tasks with Priority

#### Via Email (Priority based on sender)
- High-priority: Tasks from known senders get priority 1
- Normal: Default tasks get priority 0

#### Via API
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-project",
    "instructions": "Fix the login bug",
    "priority": 10
  }'
```

### Monitoring

#### Health Check
```bash
curl http://localhost:8000/health/status
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "uptime_seconds": 3600,
  "version": "1.0.0-alpha",
  "queue_stats": {
    "pending": 5,
    "running": 2,
    "completed": 85,
    "failed": 10
  },
  "components": {
    "email_monitor": {"status": "configured"},
    "llm_interface": {"status": "connected"},
    "task_queue": {"status": "connected"}
  }
}
```

#### Metrics
```bash
curl http://localhost:8000/metrics
```

Response:
```json
{
  "queue": {
    "pending": 5,
    "running": 2,
    "completed": 85,
    "failed": 10
  },
  "tasks": {
    "total": 100,
    "completed": 85,
    "failed": 10,
    "running": 5,
    "success_rate": 85.0
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

## 🔄 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Agent Loop Configuration
AGENT_MAX_RETRIES=3
AGENT_RETRY_DELAY=60
TASK_TIMEOUT=3600

# Priority Settings (optional)
PRIORITY_DEFAULT=0
```

### Customizing Retry Behavior

To change retry behavior, modify the environment variables:

```bash
export AGENT_MAX_RETRIES=5
export AGENT_RETRY_DELAY=120  # 2 minutes between retries
export TASK_TIMEOUT=7200      # 2 hours timeout
```

## 🧪 Testing

### Run Agent Loop Tests

```bash
source venv/bin/activate
python test_agent_loop.py
```

### Test Priority Queue

```bash
# Create tasks with different priorities
python -c "
from agent_loop import create_agent_loop
agent = create_agent_loop()

# Create low priority task
task_low = agent.queue.create_task('low', 'Low priority', priority=0)

# Create high priority task  
task_high = agent.queue.create_task('high', 'High priority', priority=10)

# Get pending tasks - should get high priority first
first = agent.queue.get_pending_task()
print(f'First task: {first[\"id\"]}')  # Should be task_high

second = agent.queue.get_pending_task()
print(f'Second task: {second[\"id\"]}')  # Should be task_low
"
```

### Test Retry Logic

```bash
# Start the system and send a failing email
# Watch logs to see retry attempts
python main.py
```

## 📊 Task Status Flow (Enhanced)

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

Retry Logic:
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ pending │────▶│ running │────▶│ running │────▶│ failed  │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
                      ▲              │
                      └── Retry Loop ──┘
```

## 🎯 Next Steps (Phase 4)

- [ ] Bash command execution capability
- [ ] Project context awareness
- [ ] Concurrent task processing (multiple workers)
- [ ] Task priority queue with dynamic reordering
- [ ] Task history analytics and reporting
- [ ] Web dashboard for real-time monitoring

## 🔧 Troubleshooting

### Tasks Stuck in Running Status

1. Check if worker process is still running:
```bash
ps aux | grep celery
```

2. Manually update task status:
```sql
UPDATE tasks SET status = 'failed' WHERE id = '{task_id}' AND status = 'running';
```

3. Restart the worker

### Retry Logic Not Working

1. Check environment variables are set correctly
2. Verify agent loop is using updated code
3. Check logs for retry attempts

### High Memory Usage

1. Reduce `TASK_TIMEOUT` to prevent long-running tasks
2. Monitor Redis memory usage if using Redis
3. Consider reducing worker concurrency

## 📚 References

- [Celery Documentation](https://docs.celeryq.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Retry Patterns](https://pypi.org/project/tenacity/)

## 🔍 Code Examples

### Custom Agent Loop with Priority

```python
from agent_loop import create_agent_loop

agent = create_agent_loop()

# Create high-priority task
task_id = agent.queue.create_task(
    project_name="urgent",
    instructions="Fix critical bug",
    priority=10  # High priority
)

# Process queue (will get high priority first)
processed = agent.process_queue(max_tasks=1)
```

### Custom Retry Configuration

```python
import os
from agent_loop import create_agent_loop

# Set custom retry configuration
os.environ['AGENT_MAX_RETRIES'] = '5'
os.environ['AGENT_RETRY_DELAY'] = '30'

agent = create_agent_loop()

print(f"Max retries: {agent.max_retries}")  # 5
print(f"Retry delay: {agent.retry_delay}")  # 30 seconds
```

## 📝 Summary

Phase 3 delivers a robust, production-ready agentic loop with:

- ✅ Retry logic with configurable attempts and delays
- ✅ Priority queue for task ordering
- ✅ Timeout protection for long-running tasks
- ✅ Comprehensive monitoring and health checks
- ✅ Enhanced error handling and logging
- ✅ API endpoints for system status and metrics

The system is now ready for production deployment with proper monitoring and failover capabilities.
