# Codemail System Startup Guide

## Quick Start (Recommended)

### Prerequisites
1. **LM Studio** must be running with a local server started
2. Python 3.12+ installed
3. Required dependencies: `pip install -r requirements.txt`

### Step-by-Step Startup

#### 1. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or your preferred editor
```

Required settings in `.env`:
```env
# Email Configuration (IMAP/SMTP)
EMAIL_ADDRESS=your_email@example.com
EMAIL_PASSWORD=your_app_password

# LLM Configuration (LM Studio local endpoint)
LLM_ENDPOINT=http://127.0.0.1:1234/v1/models

# Database Configuration
DATABASE_URL=sqlite:///tasks.db
```

#### 2. Start the System
```bash
# Make sure LM Studio is running with a local server
# Then simply run:
./start.sh
```

Or manually:
```bash
python3 main.py
```

## Available Startup Scripts

### `start.sh` - Simple Single-Process Mode (Phase 1)
The primary startup script for the current implementation.

**Features:**
- Validates LM Studio is running
- Initializes SQLite database if needed
- Starts email monitoring and task processing in a single process
- Processes tasks sequentially as they arrive

**Usage:**
```bash
./start.sh
```

### `startup.sh` - Advanced Multi-Component Mode
For future phases with distributed task processing.

**Features:**
- Validates all components (LLM, database, Redis)
- Provides multiple startup options
- Supports Celery worker mode for distributed processing

**Usage:**
```bash
./startup.sh
```

## System Modes

### 1. Single-Process Mode (Current - Phase 1)
```bash
python3 main.py
```
- Email monitoring and task execution in one process
- Tasks processed sequentially
- Simple setup, ideal for development and single-user use

### 2. API Server Only
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```
- Provides REST API endpoints for task queue status
- Can be run alongside the main process or standalone

### 3. Distributed Mode (Future - Phase 4)
```bash
# Terminal 1: Start Celery worker
celery -A worker worker --loglevel=info

# Terminal 2: Start Celery beat scheduler  
celery -A worker beat --loglevel=info

# Terminal 3: Start API server
uvicorn api_server:app --host 0.0.0.0 --port 8000
```
- Tasks processed by separate worker processes
- Supports multiple concurrent tasks (with Redis)
- Suitable for production multi-user environments

## Troubleshooting

### LLM Service Not Responding
```bash
# Test LM Studio endpoint manually
curl http://127.0.0.1:1234/v1/models

# Should return JSON with model information
```

If not responding:
1. Open LM Studio
2. Load a local model
3. Start the local server (usually on port 1234)
4. Verify the endpoint matches `LLM_ENDPOINT` in `.env`

### Database Errors
```bash
# Remove and recreate database
rm tasks.db
python3 main.py
```

### Email Connection Issues
- Verify IMAP/SMTP settings in `.env`
- For Gmail, use an App Password (not your regular password)
- Enable "Less secure app access" or use OAuth2 if needed

## Monitoring the System

Once running, you can:

1. **Check logs** - The main process outputs detailed logging
2. **API Status** - Run `uvicorn api_server:app --port 8000` and visit `http://localhost:8000/status`
3. **Task Queue** - View pending/running/completed tasks via the API

## Stopping the System

Press `Ctrl+C` in the terminal where `main.py` is running to gracefully stop the email monitor.

## Next Steps

After successful startup:
1. Send a test email with subject: `codemail: project-name`
2. Include instructions in the body
3. Monitor the logs for task processing
4. Check your inbox for completion reports
