#!/bin/bash

# MaskGate Setup Script
# This script sets up the development environment for MaskGate

set -e

echo "🚀 Setting up MaskGate development environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL 14 or higher."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Setup backend
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r ../requirements.txt

# Create .env file if it doesn't exist
if [ ! -f "../.env" ]; then
    echo "Creating .env file from .env.example..."
    cp ../.env.example ../.env
    echo "⚠️  Please update .env with your actual configuration"
fi

cd ..

# Setup frontend
echo "📦 Setting up frontend..."
cd frontend

# Install Node dependencies
echo "Installing Node dependencies..."
npm install

cd ..

# Setup database
echo "🗄️  Setting up database..."
read -p "Do you want to initialize the database? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "PostgreSQL username (default: postgres): " db_user
    db_user=${db_user:-postgres}
    
    read -sp "PostgreSQL password: " db_password
    echo
    
    read -p "Database name (default: maskgate): " db_name
    db_name=${db_name:-maskgate}
    
    # Create database
    echo "Creating database..."
    createdb -U $db_user $db_name || echo "Database may already exist"
    
    # Run schema
    echo "Running schema.sql..."
    psql -U $db_user -d $db_name -f database/schema.sql
    
    # Run seed data
    read -p "Do you want to load seed data? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Running seed.sql..."
        psql -U $db_user -d $db_name -f database/seed.sql
    fi
    
    # Update .env with database credentials
    if [ -f ".env" ]; then
        sed -i.bak "s/DB_USER=.*/DB_USER=$db_user/" .env
        sed -i.bak "s/DB_PASSWORD=.*/DB_PASSWORD=$db_password/" .env
        sed -i.bak "s/DB_NAME=.*/DB_NAME=$db_name/" .env
        rm .env.bak
    fi
fi

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update .env with your configuration (especially OPENAI_API_KEY)"
echo "2. Start backend: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo "3. Start frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:3000 in your browser"
