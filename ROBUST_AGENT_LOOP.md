# Robust Agentic Loop Implementation

This document describes the enhanced agent loop implementation with robust error handling, retry logic, priority queuing, and comprehensive monitoring.

## ✨ Features

### 1. Retry Logic with Configurable Attempts

The agent loop automatically retries failed tasks up to a configurable number of times:

```python
# Default: 3 retries with 60 second delays
agent = create_agent_loop()

# Custom configuration via environment variables:
AGENT_MAX_RETRIES=5      # Maximum retry attempts
AGENT_RETRY_DELAY=120    # Seconds between retries
```

**Behavior:**
- Tasks are retried automatically on failure
- Each attempt is logged with context
- After max retries, task is marked as failed with detailed error message

### 2. Priority Queue Support

Tasks can be created with different priorities for ordered processing:

```python
# Create high-priority task
task_id = queue.create_task(
    project_name="urgent",
    instructions="Fix critical bug",
    priority=10  # Higher number = higher priority
)

# Create normal priority task
task_id = queue.create_task(
    project_name="normal", 
    instructions="Add new feature",
    priority=0  # Default priority
)
```

**Behavior:**
- Tasks are processed in priority order (highest first)
- Within same priority, tasks are processed by creation time
- Priority is stored in database with index for efficient queries

### 3. Timeout Protection

Long-running tasks are automatically terminated:

```python
# Configure timeout via environment variable:
TASK_TIMEOUT=3600  # Default: 1 hour (in seconds)
```

**Behavior:**
- Tasks older than timeout are marked as failed
- Prevents resource exhaustion from stuck tasks
- Configurable per deployment

### 4. Comprehensive Monitoring

System health and metrics are available via API:

```bash
# Health status
curl http://localhost:8000/health/status

# Readiness probe (Kubernetes-style)
curl http://localhost:8000/health/ready

# System metrics
curl http://localhost:8000/metrics
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Loop                               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Email Monitor│  │ Task Queue   │  │ LLM Interface│      │
│  │ (IMAP)       │  │ (SQLite +    │  │ (Iterative)  │      │
│  └──────────────┘  │ Redis)       │  └──────────────┘      │
│                    └──────────────┘                         │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │ Retry Logic       │                    │
│                    │ - Max attempts    │                    │
│                    │ - Delay between   │                    │
│                    │ - Progress tracking│                   │
│                    └─────────┬─────────┘                    │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │ Priority Queue    │                    │
│                    │ - Ordered by      │                    │
│                    │ - Priority index  │                    │
│                    └─────────┬─────────┘                    │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │ Timeout Monitor   │                    │
│                    │ - Task age check  │                    │
│                    │ - Auto-fail long  │                    │
│                    └───────────────────┘                    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                     ┌─────────▼─────────┐
                     │ Monitoring API    │
                     │ - Health checks   │
                     │ - Metrics         │
                     │ - Queue stats     │
                     └───────────────────┘
```

## 🚀 Usage Examples

### Basic Task Execution with Retry

```python
from agent_loop import create_agent_loop

agent = create_agent_loop()

# Process a single task (with automatic retry)
task_id = "some-task-id"
success = agent.execute_task(task_id)

if success:
    print("Task completed successfully!")
else:
    print(f"Task failed after {agent.max_retries + 1} attempts")
```

### Priority-Based Task Processing

```python
from agent_loop import create_agent_loop

agent = create_agent_loop()

# Create high-priority task
urgent_task_id = agent.queue.create_task(
    project_name="critical",
    instructions="Fix security vulnerability",
    priority=100  # Very high priority
)

# Process queue (will get urgent task first)
processed = agent.process_queue(max_tasks=1)
```

### Custom Retry Configuration

```python
import os
from agent_loop import create_agent_loop

# Configure retry behavior
os.environ['AGENT_MAX_RETRIES'] = '5'
os.environ['AGENT_RETRY_DELAY'] = '30'  # 30 seconds between retries

agent = create_agent_loop()

print(f"Max retries: {agent.max_retries}")      # 5
print(f"Retry delay: {agent.retry_delay} sec")  # 30
```

### Monitoring System Health

```python
from monitoring import create_monitor, create_health_check_api

monitor = create_monitor()
health_api = create_health_check_api()

# Get comprehensive health status
status = monitor.get_system_status()
print(f"System status: {status['status']}")

# Check individual components
for component, info in status['components'].items():
    print(f"{component}: {info['status']}")
```

## 📝 API Endpoints

### Health Status
```bash
GET /health/status
```
Returns comprehensive system health including all components.

### Readiness Probe
```bash
GET /health/ready
```
Returns readiness status for Kubernetes-style deployment.

### Metrics
```bash
GET /metrics
```
Returns system metrics and statistics.

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MAX_RETRIES` | 3 | Maximum retry attempts per task |
| `AGENT_RETRY_DELAY` | 60 | Seconds between retry attempts |
| `TASK_TIMEOUT` | 3600 | Maximum task execution time (seconds) |
| `PRIORITY_DEFAULT` | 0 | Default priority for new tasks |

### Database Schema

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
    priority INTEGER DEFAULT 0,  -- NEW FIELD
    INDEX idx_tasks_priority (priority DESC)  -- NEW INDEX
)
```

## 🧪 Testing

### Run Agent Loop Tests

```bash
source venv/bin/activate
python test_agent_loop.py -v
```

### Test Priority Queue

```bash
# Create tasks with different priorities and verify ordering
python -c "
from agent_loop import create_agent_loop
agent = create_agent_loop()

# Create high priority task
task_high = agent.queue.create_task('high', 'High priority', priority=10)

# Create low priority task
task_low = agent.queue.create_task('low', 'Low priority', priority=0)

# Get pending tasks - should get high priority first
first = agent.queue.get_pending_task()
print(f'First task priority: {first[\"priority\"]}')  # Should be 10
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

## 🔍 Troubleshooting

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

## 🔧 Migration Guide

### Upgrading Existing Databases

Run the migration script to add priority column:

```bash
source venv/bin/activate
python migrate_priority.py
```

This will:
1. Add `priority` column to tasks table
2. Set default value of 0 for existing tasks
3. Create index for efficient priority queries

## 📝 Summary

The robust agentic loop implementation provides:

- ✅ Automatic retry with configurable attempts and delays
- ✅ Priority-based task ordering
- ✅ Timeout protection for long-running tasks
- ✅ Comprehensive monitoring and health checks
- ✅ Enhanced error handling and logging
- ✅ Production-ready reliability features
