#!/bin/bash

# Codemail System - Simple Startup Script
# For Phase 1: Single-process email monitoring with inline task execution

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Codemail System Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[!]${NC} No .env file found"
    if [ -f ".env.example" ]; then
        echo -e "${GREEN}[✓]${NC} Copying .env.example to .env..."
        cp .env.example .env
        echo -e "${YELLOW}[!]${NC} Please edit .env with your credentials before starting"
        exit 1
    else
        echo -e "${RED}[✗]${NC} Cannot find .env or .env.example"
        exit 1
    fi
fi

# Load environment variables
set -a
source .env
set +a

echo -e "${GREEN}[✓]${NC} Configuration loaded"

# Validate LM Studio is running
echo ""
echo -e "${BLUE}Checking LLM Service...${NC}"

LLM_ENDPOINT="${LLM_ENDPOINT:-http://127.0.0.1:1234/v1/models}"
LLM_BASE_URL=$(echo "$LLM_ENDPOINT" | sed 's|/v1/models||')

if curl -s --connect-timeout 5 "${LLM_BASE_URL}" > /dev/null 2>&1; then
    echo -e "${GREEN}[✓]${NC} LLM service is running at ${LLM_BASE_URL}"
else
    echo -e "${RED}[✗]${NC} LLM service at ${LLM_BASE_URL} is not responding!"
    echo -e "${YELLOW}[!]${NC} Please ensure LM Studio is running with a local server started"
    exit 1
fi

# Initialize database if needed
echo ""
echo -e "${BLUE}Initializing Database...${NC}"

if [[ "$DATABASE_URL" == sqlite://* ]]; then
    DB_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite:///||')
    
    if [ ! -f "$DB_PATH" ]; then
        echo -e "${GREEN}[✓]${NC} Creating database: $DB_PATH"
        python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

db_url = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
engine = create_engine(db_url)
with engine.connect() as conn:
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
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)'))
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)'))
"
    else
        echo -e "${GREEN}[✓]${NC} Database found: $DB_PATH"
    fi
else
    echo -e "${GREEN}[✓]${NC} Using external database"
fi

# Start the system
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   Starting Codemail System...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}[!]${NC} Press Ctrl+C to stop the email monitor"
echo ""

python3 main.py
