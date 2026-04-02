# 📧 Codemail Quick Reference

## ✅ Valid Subject Lines

Use this exact format in your email subject:

```
codemail:[project-name] instructions
```

### Examples:
- `codemail:[my-web-app] Fix login button styling`
- `CODEMAIL:[api-service] Add rate limiting`
- `Codemail: [frontend-app] Update navigation menu`

## ❌ Invalid Subject Lines (Will Be Ignored)

- `[my-project] Fix bug` - Missing prefix
- `codemail my-project Fix bug` - No brackets
- `codemail: Fix bug` - No project name

## 📝 Email Format

### Subject
```
codemail:[project-name] brief instructions
```

### Body (Optional but Recommended)
```
Detailed instructions for the AI agent...

Requirements:
1. Step one
2. Step two  
3. Step three

Files to modify:
- file1.py
- file2.js

Additional context...
```

## ⚙️ Configuration

Set environment variables in `.env`:

```env
# Email (required)
IMAP_HOST=imap.gmail.com
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# LLM (required for task execution)
LLM_ENDPOINT=http://127.0.0.1:1234/v1/models

# Optional - customize prefix
CODEMAIL_PREFIX=codemail:
```

## 🚀 Quick Start

```bash
# 1. Install dependencies
./setup.sh

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run codemail
source venv/bin/activate
python main.py
```

## 🔍 Testing

```bash
# Full system test (includes all components)
python test_system.py
```

## 📊 Status API

Start the web interface:
```bash
python api_server.py
```
Access at: http://localhost:8000/docs

## 📁 Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point, email monitoring loop |
| `email_monitor.py` | IMAP email checking |
| `subject_validator.py` | Subject line validation |
| `email_parser.py` | Parse email content |
| `agent_loop.py` | Task execution orchestration |
| `task_queue.py` | SQLite task storage |
| `llm_interface.py` | LLM API integration |

## 🎯 Common Tasks

### Add New Feature
```
Subject: codemail:[my-app] Implement dark mode toggle

Body:
Add a dark mode toggle in the settings page.
Store preference in localStorage.
Use CSS variables for theme colors.
```

### Fix Bug
```
Subject: codemail:[frontend] Fix navigation menu on mobile

Body:
The navigation menu doesn't collapse properly on mobile devices.
Test on Chrome and Safari before committing.
```

### Refactor Code
```
Subject: codemail:[backend] Optimize database queries

Body:
Optimize the user query in src/models/user.py.
Add indexes for frequently queried fields.
Run performance tests before submitting.
```

## 🔧 Troubleshooting

### Email Not Being Processed?
1. Check subject matches `codemail:[project-name] instructions`
2. Verify email credentials in `.env`
3. Check logs: `tail -f logs/codemail.log`

### LLM Not Responding?
1. Ensure LM Studio server is running
2. Verify `LLM_ENDPOINT` in `.env`
3. Test endpoint: `curl http://127.0.0.1:1234/v1/models`

### Task Stuck in Queue?
1. Check task status via API
2. Review agent loop logs
3. Restart codemail system

## 📞 Support

- **Logs**: `logs/codemail.log`
- **API Docs**: http://localhost:8000/docs
- **Tests**: Run `python test_system.py`

---

**Quick Tip**: Always test your subject line format before sending to production!
