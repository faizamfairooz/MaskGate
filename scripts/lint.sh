#!/bin/bash

# MaskGate Lint Script
# This script runs linting on both backend and frontend code

echo "🔍 Running lint checks..."

# Backend linting
echo "📦 Linting backend code..."
cd backend

if [ -d "venv" ]; then
    source venv/bin/activate
    
    # Install linting tools if not present
    pip install flake8 black isort mypy 2>/dev/null || true
    
    echo "Running flake8..."
    flake8 app/ --max-line-length=100 --ignore=E203,W503 || echo "⚠️  Flake8 found issues"
    
    echo "Running black (check)..."
    black --check app/ || echo "⚠️  Black found formatting issues"
    
    echo "Running isort (check)..."
    isort --check-only app/ || echo "⚠️  isort found import issues"
    
    echo "Running mypy..."
    mypy app/ --ignore-missing-imports || echo "⚠️  mypy found type issues"
    
    cd ..
else
    echo "⚠️  Backend virtual environment not found, skipping backend lint"
    cd ..
fi

# Frontend linting
echo "🎨 Linting frontend code..."
cd frontend

if [ -d "node_modules" ]; then
    echo "Running ESLint..."
    npm run lint || echo "⚠️  ESLint found issues"
    
    cd ..
else
    echo "⚠️  Frontend dependencies not installed, skipping frontend lint"
    cd ..
fi

echo ""
echo "✅ Lint checks complete!"
echo "Review the warnings above and fix any issues"
