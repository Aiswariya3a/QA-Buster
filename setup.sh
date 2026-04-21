#!/bin/bash

# QA-Buster Local Development Setup Script
# Run this script to set up your development environment

echo "QA-Buster Development Setup"
echo "================================"

# Check Python version
echo "Checking Python version..."
python3 --version || {
    echo "Python 3 not found. Please install Python 3.8+"
    exit 1
}

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy .env.example to .env
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update .env with your Google Sheet CSV_URL"
else
    echo ".env already exists"
fi

# Create static directory if it doesn't exist
mkdir -p static

# Initialize database
echo "Initializing database..."
python3 -c "from database import init_db; init_db(); print('✓ Database initialized')"

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update CSV_URL in .env with your Google Sheet"
echo "2. Start LM Studio on localhost:1234 (optional)"
echo "3. Run: python main.py"
echo ""
