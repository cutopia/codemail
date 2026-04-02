# Codemail Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   ./setup.sh
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start the System**
   ```bash
   source venv/bin/activate
   python main.py
   ```

## Detailed Configuration

### Email Setup

#### For Gmail:
1. Enable 2-Factor Authentication on your Google Account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and your device
   - Copy the generated password
3. Update `.env`:
   ```
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```

#### For Other Email Providers:
- **Outlook/Hotmail**: `imap-mail.outlook.com`, `smtp-mail.outlook.com`
- **Yahoo**: `imap.mail.yahoo.com`, `smtp.mail.yahoo.com`
- Check your provider's IMAP/SMTP settings documentation

### LLM Setup (LM Studio)

1. **Install LM Studio**
   - Download from [lmstudio.ai](https://lmstudio.ai/)
   - Install and launch the application

2. **Download a Model**
   - Open LM Studio
   - Go to "Model Hub"
   - Select a model (recommended: Llama-3-8B, Mistral-7B)
   - Click "Download"

3. **Start Local Server**
   - Load your downloaded model
   - Click "Server" tab
   - Click "Start Server"
   - Default endpoint: `http://127.0.0.1:1234/v1/models`

4. **Configure Codemail**
   ```
   LLM_ENDPOINT=http://127.0.0.1:1234/v1/models
   LLM_API_KEY=dummy_key  # LM Studio doesn't require real API key locally
   ```

### Testing the Setup

#### Test Email Parser:
```bash
python -c "
from email_parser import create_email_parser
parser = create_email_parser()
email = {'subject': '[test] hello', 'body': 'world'}
print(parser.parse_email(email))
"
```

#### Test Task Queue:
```bash
python -c "
from task_queue import create_task_queue
queue = create_task_queue()
task_id = queue.create_task('test', 'test instructions')
print(f'Created task: {task_id}')
tasks = queue.get_all_tasks()
print(f'Total tasks: {len(tasks)}')
"
```

#### Test LLM Connection:
```bash
python -c "
from llm_interface import create_llm_interface
llm = create_llm_interface()
print('Connected:', llm.check_connection())
"
```

## Usage Examples

### Sending a Task Email

**Subject:** `[my-project] Implement a feature`

**Body:**
```
Project: my-project

Please implement a function that:
1. Takes a list of numbers as input
2. Returns the sum of all even numbers
3. Handles edge cases like empty lists
4. Includes unit tests
```

Or simply use brackets in subject:
```
[my-project] Create a Python script to calculate Fibonacci sequence
```

### Checking Task Status

```python
from task_queue import create_task_queue

queue = create_task_queue()

# Get all tasks
all_tasks = queue.get_all_tasks()
for task in all_tasks:
    print(f"Task {task['id'][:8]}...: {task['status']}")

# Get specific task
task = queue.get_task("your-task-id")
print(f"Output: {task['output']}")
```

## Troubleshooting

### Email Connection Issues
- Verify IMAP/SMTP settings are correct
- Check that app password is generated correctly
- Ensure "Less secure app access" is enabled if needed
- Test with `python -c "import imaplib; ..."` manually

### LLM Connection Issues
- Verify LM Studio server is running
- Check endpoint URL matches LM Studio configuration
- Ensure no firewall blocking localhost connections
- Test with curl: `curl http://127.0.0.1:1234/v1/models`

### Database Errors
- Delete `tasks.db` to reset database
- Ensure write permissions in current directory
- Check SQLite is installed: `python -c "import sqlite3"`

## Advanced Configuration

### Changing Poll Interval
Edit `main.py`:
```python
monitor.monitor_loop(callback=email_callback, poll_interval=30)  # Check every 30 seconds
```

### Using PostgreSQL Instead of SQLite
Update `.env`:
```
DATABASE_URL=postgresql://user:password@localhost/codemail
```

### Running with Celery (Future Enhancement)
```bash
# Start Redis
redis-server

# Start Celery worker
celery -A task_queue.celery_app worker --loglevel=info

# Start main application
python main.py
```

## Next Steps

1. **Phase 2**: Add more sophisticated email parsing
2. **Phase 3**: Implement bash command execution
3. **Phase 4**: Add Celery for concurrent task processing
4. **Phase 5**: Create REST API for status monitoring

## Support

For issues or questions:
- Check logs in `logs/codemail.log`
- Review error messages in console output
- Test individual components before full integration
