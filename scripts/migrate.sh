#!/bin/bash

# MaskGate Database Migration Script
# This script handles database migrations and schema updates

set -e

echo "🗄️  Running database migrations..."

# Load database configuration from .env
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

# Check required variables
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    echo "❌ Database configuration not found in .env"
    exit 1
fi

# Function to run SQL file
run_sql() {
    local file=$1
    echo "📝 Running $file..."
    psql -U "$DB_USER" -d "$DB_NAME" -f "$file"
}

# Check for migration files
MIGRATIONS_DIR="../database/migrations"
if [ -d "$MIGRATIONS_DIR" ]; then
    echo "📁 Found migrations directory"
    
    # Run migration files in order
    for migration in $(ls "$MIGRATIONS_DIR"/*.sql | sort); do
        run_sql "$migration"
    done
else
    echo "ℹ️  No migrations directory found, running initial schema..."
    run_sql "../database/schema.sql"
fi

echo "✅ Migrations complete!"
