#!/bin/bash

# Codemail Setup Script
# This script sets up the environment and installs dependencies

set -e  # Exit on error

echo "=== Codemail Setup ==="

# Check Python version
echo "Checking Python version..."
python3 --version || python --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Copy example config if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env with your email credentials and LLM endpoint."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Run 'python test_system.py' to test components"
echo "3. Run 'python main.py' to start the system"
