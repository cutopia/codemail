#!/bin/bash

# Codemail System Startup Script
# This script starts all necessary components of the Codemail system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Codemail System Startup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning "No .env file found. Please create one from .env.example"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

echo -e "${BLUE}Loading configuration...${NC}"
print_status "Email: ${EMAIL_ADDRESS:-not set}"
print_status "LLM Endpoint: ${LLM_ENDPOINT:-http://127.0.0.1:1234/v1/models}"
print_status "Database: ${DATABASE_URL:-sqlite:///tasks.db}"
echo ""

# Step 1: Validate LM Studio is running
echo -e "${BLUE}Step 1: Validating LLM Service...${NC}"

LLM_ENDPOINT="${LLM_ENDPOINT:-http://127.0.0.1:1234/v1/models}"

# Extract just the base URL (remove /v1/models if present)
LLM_BASE_URL=$(echo "$LLM_ENDPOINT" | sed 's|/v1/models||')

if curl -s --connect-timeout 5 "${LLM_BASE_URL}" > /dev/null 2>&1; then
    print_status "LLM service is running at ${LLM_BASE_URL}"
    
    # Try to get models list to confirm full functionality
    if curl -s --connect-timeout 5 "${LLM_ENDPOINT}" | grep -q "models"; then
        print_status "LLM API is responding with model information"
    else
        print_warning "LLM endpoint responded but model info not confirmed"
    fi
else
    print_error "LLM service at ${LLM_BASE_URL} is not responding!"
    print_error "Please ensure LM Studio is running and the local server is started."
    exit 1
fi

echo ""

# Step 2: Check database setup
echo -e "${BLUE}Step 2: Checking Database...${NC}"

if [[ "$DATABASE_URL" == sqlite://* ]]; then
    # SQLite database
    DB_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite:///||')
    
    if [ ! -f "$DB_PATH" ]; then
        print_status "Creating new SQLite database: $DB_PATH"
        python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

db_url = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
engine = create_engine(db_url)
with engine.connect() as conn:
    # Create tasks table if it doesn't exist
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            project_name TEXT NOT NULL,
            instructions TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            sender TEXT,
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            output TEXT,
            error TEXT
        )
    '''))
    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
    '''))
    conn.execute(text('''
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)
    '''))
    
print('Database initialized successfully')
"
        print_status "SQLite database created: $DB_PATH"
    else
        print_status "SQLite database found: $DB_PATH"
    fi
else
    # PostgreSQL or other database
    print_status "Using external database: ${DATABASE_URL}"
fi

echo ""

# Step 3: Check Redis connection (if configured)
echo -e "${BLUE}Step 3: Checking Redis Connection...${NC}"

REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

if command -v redis-cli &> /dev/null; then
    if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
        print_status "Redis is running and accessible"
    else
        print_warning "Redis is not running or not configured. Using database-only mode."
        print_warning "For distributed task processing, start Redis: redis-server"
    fi
else
    print_warning "redis-cli not found. Skipping Redis validation."
fi

echo ""

# Step 4: Display startup options
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Startup Options${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}1. Full System (Email Monitor + API)${NC}"
echo "   python3 main.py"
echo "   - Starts email monitoring and task processing"
echo "   - Processes tasks sequentially in the main process"
echo ""

echo -e "${GREEN}2. Celery Distributed Mode${NC}"
echo "   # Terminal 1: Start Celery worker"
echo "   celery -A worker worker --loglevel=info"
echo ""
echo "   # Terminal 2: Start Celery beat scheduler"
echo "   celery -A worker beat --loglevel=info"
echo ""

echo -e "${GREEN}3. API Server Only${NC}"
echo "   uvicorn api_server:app --host 0.0.0.0 --port 8000"
echo "   - Provides REST API for task queue status"
echo ""

echo -e "${GREEN}4. Quick Start (Recommended)${NC}"
echo "   # Terminal 1: Email Monitor + Agent Loop"
echo "   python3 main.py"
echo ""
echo "   # Terminal 2: API Server (optional, for monitoring)"
echo "   uvicorn api_server:app --host 0.0.0.0 --port 8000"
echo ""

# Step 5: Start the system
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Starting Codemail System${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
print_status "System is ready to start!"
echo ""
print_warning "Press Ctrl+C to stop the email monitor"
echo ""

# Start the main application
python3 main.py
