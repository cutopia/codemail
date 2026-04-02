# Phase 2 Quick Reference

## Core Commands

### Start System (No Redis)
```bash
source venv/bin/activate
python main.py
```

### Start Celery Worker (With Redis)
```bash
redis-server &
celery -A celery_app worker --loglevel=info
```

### Start API Server
```bash
source venv/bin/activate
python api_server.py
```

## API Endpoints

### Create Task
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_name": "my-project", "instructions": "Fix the bug"}'
```

### Get Queue Status
```bash
curl http://localhost:8000/queue/status
```

### Monitor Task Progress
```bash
curl http://localhost:8000/tasks/{task_id}/progress
```

### Stop Running Task
```bash
curl -X PATCH http://localhost:8000/tasks/{task_id}/stop
```

## Environment Variables

### Required (Phase 1)
```env
IMAP_HOST=imap.gmail.com
SMTP_HOST=smtp.gmail.com
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
LLM_ENDPOINT=http://127.0.0.1:1234/v1/models
DATABASE_URL=sqlite:///tasks.db
```

### Optional (Phase 2)
```env
REDIS_URL=redis://localhost:6379/0
CODEMAIL_PREFIX=codemail:
```

## Task Status Flow

```
pending → running → completed
         ↘ failed
          ↘ stopped
```

## Celery Commands

### Start Worker
```bash
celery -A celery_app worker --loglevel=info
```

### Start Beat Scheduler
```bash
celery -A celery_app beat --loglevel=info
```

### Check Worker Status
```bash
celery -A celery_app inspect active
```

## Database Queries

### View All Tasks
```bash
sqlite3 tasks.db "SELECT id, project_name, status FROM tasks ORDER BY created_at DESC;"
```

### View Pending Tasks
```bash
sqlite3 tasks.db "SELECT * FROM tasks WHERE status = 'pending';"
```

### Update Task Status
```sql
UPDATE tasks SET status = 'completed' WHERE id = '{task_id}';
```

## Email Format

### Subject Line
```
codemail:[project-name] instructions
```

### Examples
```
codemail:[my-web-app] Fix the login button
CODEMAIL:[api-service] Add rate limiting
Codemail: [data-pipeline] Optimize ETL process
```

## Troubleshooting

### Redis Not Available
- System falls back to SQLite-only mode
- Progress tracking disabled but all other features work
- Check logs for warnings (not errors)

### Celery Worker Not Starting
1. Ensure Redis is running: `redis-cli ping`
2. Check worker command: `celery -A celery_app worker --loglevel=info`
3. Verify environment variables are loaded

### Task Stuck in Running
```bash
# Update task status manually
sqlite3 tasks.db "UPDATE tasks SET status = 'failed' WHERE id = '{task_id}' AND status = 'running';"
```

## File Structure

```
codemail/
├── celery_app.py      # Celery configuration (NEW)
├── worker.py          # Celery worker (NEW)
├── task_queue.py      # Enhanced with Redis
├── agent_loop.py      # Progress callbacks
├── llm_interface.py   # Progress support
├── api_server.py      # New endpoints
└── requirements.txt   # Updated deps
```

## Testing

### Test Components
```bash
# Task queue
python -c "from task_queue import create_task_queue; q = create_task_queue(); print(q.get_queue_stats())"

# Celery app
python -c "from celery_app import celery_app; print(celery_app.conf.broker_url)"

# API server
python api_server.py
```

### Run Full Test Suite
```bash
source venv/bin/activate
python test_system.py
```

## Key Features

| Feature | SQLite Only | With Redis |
|---------|-------------|------------|
| Task Queue | ✅ | ✅ |
| Email Processing | ✅ | ✅ |
| Progress Tracking | ❌ | ✅ |
| Distributed Processing | ❌ | ✅ |
| Real-time Monitoring | ❌ | ✅ |

## Next Steps

1. Install Redis for enhanced functionality
2. Configure Celery workers for distributed processing
3. Set up monitoring and alerting
4. Implement bash command execution (Phase 3)

---

**Status**: Phase 2 Complete ✅  
**Version**: 0.2.0-alpha  
**Last Updated**: April 2026
