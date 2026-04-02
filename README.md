# 📧 Codemail - Email-Driven Coding Agent

Codemail is a system that allows you to control a self-hosted LLM and coding agent remotely by sending emails with instructions. The system monitors incoming emails, processes tasks in an agentic loop, and reports back via email.

## ✨ Features

- 📧 **Email-based interface** - Send instructions via email to trigger coding tasks
- 🤖 **LLM-powered agent** - Uses local LLM (LM Studio) for intelligent task execution  
- 🔁 **Iterative refinement** - Agent refines its own output for better results
- 📊 **Task queue system** - Manages multiple tasks with status tracking
- 📧 **Email reports** - Get completion reports sent back to your inbox
- 🌐 **REST API** - Monitor and manage tasks via web interface

## 🚀 Quick Start

### 1. Install Dependencies

```bash
./setup.sh
```

### 2. Configure Environment

Edit `.env` with your credentials:

```env
# Email Configuration
IMAP_HOST=imap.gmail.com
SMTP_HOST=smtp.gmail.com
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# LLM Configuration (LM Studio)
LLM_ENDPOINT=http://127.0.0.1:1234/v1/models
LLM_API_KEY=dummy_key
```

### 3. Start the System

```bash
source venv/bin/activate
python main.py
```

## 📖 Detailed Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Comprehensive setup instructions
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current development status and roadmap

## 🎯 How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Email Monitor │────▶│  Task Queue      │────▶│  Agent Loop     │
│ (IMAP)          │     │  (SQLite)        │     │  (Agentic)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                        │                      │
         ▼                        ▼                      ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Email Sender  │     │  Task Database   │     │  LLM Interface  │
│ (SMTP)          │     │  (tasks.db)      │     │  (LM Studio)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Status API     │
│  (FastAPI)      │
└─────────────────┘
```

## 📧 Email Format

Send an email with instructions:

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

## 🌐 REST API

Start the API server:

```bash
python api_server.py
```

Access documentation at: http://localhost:8000/docs

### Available Endpoints

- `GET /` - System status
- `GET /tasks` - List all tasks
- `GET /tasks/{task_id}` - Get specific task
- `POST /tasks` - Create new task
- `PATCH /tasks/{task_id}/status` - Update task status
- `DELETE /tasks/{task_id}` - Delete task
- `GET /queue/status` - Queue statistics

## 🧪 Testing

Run the test suite:

```bash
source venv/bin/activate
python test_system.py
```

Test individual components:

```bash
# Test email parsing
python -c "from email_parser import create_email_parser; parser = create_email_parser(); print(parser.parse_email({'subject': '[test] hello', 'body': 'world'}))"

# Test task queue
python -c "from task_queue import create_task_queue; q = create_task_queue(); print(q.get_all_tasks())"
```

## 📁 Project Structure

```
codemail/
├── main.py              # Entry point with email monitoring loop
├── config.py            # Configuration management
├── logger.py            # Logging setup and configuration
├── email_monitor.py     # IMAP email monitoring
├── email_parser.py      # Email content parsing
├── llm_interface.py     # LLM API integration
├── email_reporter.py    # SMTP email sending
├── task_queue.py        # SQLite task storage
├── agent_loop.py        # Task execution orchestration
├── workflow.py          # Complete workflow implementation
├── api_server.py        # REST API server
├── test_system.py       # Component testing suite
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── setup.sh             # Automated setup script
├── README.md            # This file
├── SETUP_GUIDE.md       # Detailed setup instructions
└── PROJECT_STATUS.md    # Development status and roadmap
```

## 🔧 Configuration

### Email Setup (Gmail Example)

1. Enable 2-Factor Authentication on your Google Account
2. Generate an App Password:
   - Go to Google Account → Security → App passwords
   - Select "Mail" and your device
   - Copy the generated password
3. Update `.env` with your email and app password

### LLM Setup (LM Studio)

1. Install [LM Studio](https://lmstudio.ai/)
2. Download a model (recommended: Llama-3-8B, Mistral-7B)
3. Start the local server (default: `http://127.0.0.1:1234/v1/models`)
4. Verify endpoint works: `curl http://127.0.0.1:1234/v1/models`

## 📊 Task Status Flow

```
pending → running → completed
         ↘ failed (error)
```

### Status Meanings

- **pending** - Task is queued and waiting for execution
- **running** - Task is currently being processed by the agent
- **completed** - Task finished successfully with output
- **failed** - Task encountered an error during execution

## 🛠️ Development

### Current Phase: Phase 1 Complete ✅

- ✅ Email monitoring and parsing
- ✅ Basic LLM integration  
- ✅ Task queue with SQLite
- ✅ Email reporting system
- ✅ REST API endpoints

### Next Steps (Phase 2)

- 🔄 Enhanced task management
- 🔄 Bash command execution
- 🔄 Project context awareness
- 🔄 Concurrent task processing

## 🔒 Security Notes

- Never commit `.env` file (included in `.gitignore`)
- Use app passwords instead of regular passwords
- Store sensitive data in environment variables
- Validate all input from emails before processing

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For issues or questions:

1. Check the logs in `logs/codemail.log`
2. Review error messages in console output
3. Test individual components before full integration
4. Open an issue on GitHub with detailed information

---

**Status**: Phase 1 Complete ✅ | Phase 2 In Progress 🔄  
**Version**: 0.1.0-alpha  
**Last Updated**: April 2026
