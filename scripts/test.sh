#!/bin/bash

# MaskGate Test Script
# This script runs the test suite for the backend

echo "🧪 Running MaskGate test suite..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies if not already installed
echo "📦 Ensuring test dependencies are installed..."
pip install pytest pytest-asyncio pytest-cov

# Run tests
echo "🧪 Running tests..."
pytest tests/ -v -m "not integration" --cov=app --cov-report=term

echo ""
echo "✅ Tests complete!"
echo "HTML coverage report available in backend/htmlcov/index.html"
