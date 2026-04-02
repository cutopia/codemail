# 🚀 Codemail Quick Start Guide

Get up and running with Codemail in 5 minutes.

## Step 1: Install Dependencies

```bash
./setup.sh
```

This will:
- Create a virtual environment
- Install all Python dependencies
- Set up the project structure

## Step 2: Configure Your Credentials

Edit `.env` with your email and LLM settings:

```env
# Email Configuration (Gmail example)
IMAP_HOST=imap.gmail.com
SMTP_HOST=smtp.gmail.com
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# LLM Configuration (LM Studio)
LLM_ENDPOINT=http://127.0.0.1:1234/v1/models
LLM_API_KEY=dummy_key
```

### Getting Gmail App Password:
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Create an App Password for "Mail"
4. Use the 16-character password in `.env`

## Step 3: Set Up LM Studio

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Open LM Studio and download a model (e.g., Llama-3-8B)
3. Click "Server" tab → "Start Server"
4. Default endpoint: `http://127.0.0.1:1234/v1/models`

## Step 4: Verify the System

```bash
source venv/bin/activate
python verify_system.py
```

You should see:
```
✅ PASS: Environment Configuration
✅ PASS: Email Parser
✅ PASS: Task Queue
✅ PASS: LLM Interface
✅ PASS: Integration

🎉 All verification checks passed!
```

## Step 5: Start the System

```bash
python main.py
```

The system will now:
- Monitor your email inbox every 60 seconds
- Process incoming emails for instructions
- Execute tasks using the LLM agent
- Send completion reports back to your email

## 📧 Sending Your First Task

Send an email with:

**Subject:** `[my-project] Implement a feature`

**Body:**
```
Project: my-project

Please implement a Python function that:
1. Takes two numbers as input
2. Returns their sum
3. Includes error handling for non-numeric inputs
4. Has unit tests
```

Or simply use brackets in subject:
```
[my-project] Create a Fibonacci sequence calculator
```

## 🌐 Monitor Tasks via API

Start the API server in another terminal:

```bash
python api_server.py
```

Access at: http://localhost:8000/docs

### Example API Commands:

```bash
# Check queue status
curl http://localhost:8000/queue/status

# List all tasks
curl http://localhost:8000/tasks

# Get specific task
curl http://localhost:8000/tasks/{task-id}
```

## 🧪 Quick Tests

### Test Email Parser
```bash
python -c "
from email_parser import create_email_parser
parser = create_email_parser()
email = {'subject': '[test] hello', 'body': 'world'}
print(parser.parse_email(email))
"
```

### Test Task Queue
```bash
python -c "
from task_queue import create_task_queue
q = create_task_queue()
task_id = q.create_task('test', 'test instructions')
print(f'Created task: {task_id}')
tasks = q.get_all_tasks()
print(f'Total tasks: {len(tasks)}')
"
```

## 📊 What to Expect

### When You Send an Email:

1. **Email arrives** → System detects new email
2. **Parsing** → Extracts project name and instructions
3. **Task creation** → Creates unique task ID in database
4. **Execution** → LLM processes instructions iteratively
5. **Reporting** → Sends completion report back to your inbox

### Email Report Contains:
- Task status (completed/failed)
- Execution time
- Output/results from LLM
- Any errors encountered

## 🔧 Troubleshooting

### "Email connection failed"
- Verify IMAP settings are correct
- Check app password is generated properly
- Ensure 2FA is enabled on your account

### "LLM endpoint not reachable"
- Start LM Studio server
- Verify endpoint URL matches LM Studio configuration
- Check no firewall blocking localhost connections

### "Tasks not processing"
- Check logs in `logs/codemail.log`
- Verify database file exists (`tasks.db`)
- Ensure LLM is running and accessible

## 📝 Next Steps

1. **Configure your email** in `.env`
2. **Set up LM Studio** with a model
3. **Run verification**: `python verify_system.py`
4. **Start monitoring**: `python main.py`
5. **Send a test email** to trigger a task
6. **Monitor via API**: http://localhost:8000/docs

## 🎯 Success Indicators

✅ System starts without errors  
✅ Email monitor connects successfully  
✅ New emails are detected and processed  
✅ LLM executes tasks and returns results  
✅ Completion reports arrive in your inbox  

---

**Time to get started**: ~5 minutes  
**Minimum requirements**: Python 3.12+, LM Studio running locally  
**Next phase**: Configure advanced features (Phase 2)
