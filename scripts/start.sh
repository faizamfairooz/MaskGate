#!/bin/bash

# MaskGate Start Script
# This script starts both backend and frontend development servers

echo "🚀 Starting MaskGate development servers..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run ./scripts/setup.sh first"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start backend
echo "📡 Starting backend server..."
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo "✅ Backend server started on http://localhost:8000"
else
    echo "❌ Backend virtual environment not found. Please run ./scripts/setup.sh first"
    exit 1
fi
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend
if [ -d "node_modules" ]; then
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ Frontend server started on http://localhost:3000"
else
    echo "❌ Frontend dependencies not installed. Please run ./scripts/setup.sh first"
    kill $BACKEND_PID
    exit 1
fi
cd ..

echo ""
echo "✨ Both servers are running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for processes
wait
