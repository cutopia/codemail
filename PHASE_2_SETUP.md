# Phase 2 Setup Guide

This guide will help you set up and run the enhanced task queue system with Celery and Redis integration.

## Prerequisites

- Python 3.12+
- Virtual environment (venv)
- Dependencies installed from `requirements.txt`

## Installation Steps

### 1. Install Dependencies

```bash
cd /home/dev/opencodeprojects/codemail
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit your `.env` file:

```env
# Email Configuration (Phase 1)
IMAP_HOST=imap.gmail.com
SMTP_HOST=smtp.gmail.com
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# LLM Configuration (Phase 1)
LLM_ENDPOINT=http://127.0.0.1:1234/v1/models
LLM_API_KEY=dummy_key

# Task Database (Phase 1)
DATABASE_URL=sqlite:///tasks.db

# Redis Configuration (Phase 2 - Optional but recommended)
REDIS_URL=redis://localhost:6379/0

# Codemail Settings
CODEMAIL_PREFIX=codemail:
```

### 3. Install and Start Redis (Optional)

#### Option A: Install Redis Locally

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS with Homebrew:**
```bash
brew install redis
brew services start redis
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

#### Option B: Use Docker

```bash
docker run -d --name codemail-redis -p 6379:6379 redis:alpine
```

#### Option C: SQLite Only (No Redis)

If you don't want to install Redis, the system will fall back to SQLite-only mode with limited functionality:
- No real-time progress tracking
- No distributed task processing
- Single-task execution only

## Running the System

### Method 1: Direct Execution (Single Task Mode)

This method processes one task at a time and doesn't require Redis.

```bash
source venv/bin/activate
python main.py
```

**How it works:**
1. Monitors email inbox for new messages
2. Parses emails with `codemail:` prefix
3. Creates tasks in the SQLite database
4. Executes each task sequentially
5. Sends completion reports via email

### Method 2: Celery Worker (Distributed Mode)

This method uses Redis and Celery for distributed task processing.

#### Start Redis Server

```bash
redis-server
```

#### Start Celery Worker

```bash
source venv/bin/activate
celery -A celery_app worker --loglevel=info
```

Or use the provided script:

```bash
python worker.py --worker
```

**How it works:**
1. Tasks are created via API or email monitoring
2. Celery worker picks up tasks from the queue
3. Each task is processed independently
4. Progress is tracked in Redis
5. Multiple workers can process tasks concurrently

### Method 3: Combined Mode (Email + Celery)

Run both email monitoring and Celery worker:

**Terminal 1 - Email Monitor:**
```bash
source venv/bin/activate
python main.py
```

**Terminal 2 - Celery Worker:**
```bash
source venv/bin/activate
celery -A celery_app worker --loglevel=info
```

## API Server

Start the REST API server to monitor and manage tasks:

```bash
source venv/bin/activate
python api_server.py
```

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System status |
| `/tasks` | GET | List all tasks |
| `/tasks/{task_id}` | GET | Get specific task |
| `/tasks` | POST | Create new task |
| `/tasks/{task_id}/status` | PATCH | Update task status |
| `/tasks/{task_id}/stop` | PATCH | Stop a running task |
| `/tasks/{task_id}/progress` | GET | Get real-time progress |
| `/queue/status` | GET | Queue statistics |

**Example Usage:**

```bash
# Create a task via API
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_name": "my-project", "instructions": "Fix the login bug"}'

# Monitor task progress
curl http://localhost:8000/tasks/{task_id}/progress

# Get queue status
curl http://localhost:8000/queue/status

# Stop a running task
curl -X PATCH http://localhost:8000/tasks/{task_id}/stop
```

## Testing the System

### Test Email Processing

1. Send an email with subject:
   ```
   codemail:[test-project] Write a hello world function
   ```

2. Check the logs for task creation and execution

3. Verify completion report is sent back to sender

### Test API Endpoints

```bash
# Start API server
python api_server.py

# In another terminal, test endpoints:
curl http://localhost:8000/queue/status
```

### Test Celery Worker

1. Start Redis server
2. Start Celery worker in one terminal
3. Create a task via API in another terminal
4. Monitor the worker terminal for task processing

## Troubleshooting

### Redis Connection Issues

**Error:** `Error 111 connecting to localhost:6379. Connection refused.`

**Solution:**
1. Ensure Redis is running: `redis-cli ping`
2. Check Redis URL in `.env`: `REDIS_URL=redis://localhost:6379/0`
3. Verify network connectivity to Redis server

### Celery Worker Not Processing Tasks

**Symptoms:** Tasks are created but not processed.

**Solution:**
1. Ensure Redis is running and accessible
2. Start the worker: `celery -A celery_app worker --loglevel=info`
3. Check worker logs for errors
4. Verify task was created in database

### Task Stuck in Running Status

**Symptoms:** Task shows as "running" but doesn't complete.

**Solution:**
1. Check if the worker process is still running
2. Manually update task status:
```sql
UPDATE tasks SET status = 'failed' WHERE id = '{task_id}' AND status = 'running';
```
3. Restart the worker

### Email Monitoring Not Working

**Symptoms:** Emails are not being processed.

**Solution:**
1. Verify email credentials in `.env`
2. Check IMAP settings (host, port)
3. Ensure 2FA is enabled and app password is used
4. Check logs for connection errors

## Configuration Options

### Task Time Limit

Set maximum execution time per task:

```env
TASK_TIME_LIMIT=3600  # 1 hour in seconds
```

### Worker Prefetch Multiplier

Control how many tasks workers prefetch:

```env
WORKER_PREFETCH_MULTIPLIER=1  # Process one task at a time
```

For multiple concurrent tasks:
```env
WORKER_PREFETCH_MULTIPLIER=4  # Process up to 4 tasks concurrently
```

## Monitoring and Logging

### View Logs

**Console logs:**
```bash
python main.py 2>&1 | tee codemail.log
```

**Celery worker logs:**
```bash
celery -A celery_app worker --loglevel=info 2>&1 | tee worker.log
```

### Database Queries

View tasks in SQLite database:

```bash
sqlite3 tasks.db "SELECT id, project_name, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 10;"
```

## Next Steps

After Phase 2 setup is complete:

- [ ] Test email processing with real emails
- [ ] Configure Celery for distributed processing
- [ ] Set up monitoring and alerting
- [ ] Implement bash command execution (Phase 3)
- [ ] Add project context awareness (Phase 3)

## Support

For issues or questions:
1. Check the logs in `logs/codemail.log`
2. Review error messages in console output
3. Test individual components before full integration
4. Open an issue on GitHub with detailed information
