#!/bin/bash

# AI Learning Platform Startup Script

echo "====================================="
echo "AI Learning Platform"
echo "====================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "Creating .env file from .env.example..."
    cp backend/.env.example backend/.env
    echo "Please edit backend/.env and add your ANTHROPIC_API_KEY"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
    cd ..
else
    cd backend
    source venv/bin/activate
    cd ..
fi

echo ""
echo "Starting backend server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "To access the frontend:"
echo "  Option 1: Open frontend/index.html in your browser"
echo "  Option 2: Run 'python -m http.server 3000' in the frontend directory"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
