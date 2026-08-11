#!/bin/bash

# MaskGate Database Backup Script
# This script creates backups of the MaskGate database

set -e

echo "💾 Creating database backup..."

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

# Create backup directory if it doesn't exist
BACKUP_DIR="../backups"
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/maskgate_backup_$TIMESTAMP.sql"

# Create backup
echo "📦 Backing up database $DB_NAME..."
pg_dump -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE"

# Compress backup
echo "🗜️  Compressing backup..."
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Calculate file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "✅ Backup complete!"
echo "📁 Backup file: $BACKUP_FILE"
echo "📊 File size: $FILE_SIZE"

# Clean up old backups (keep last 7)
echo "🧹 Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t maskgate_backup_*.sql.gz | tail -n +8 | xargs -r rm
cd ../scripts

echo "📝 Kept last 7 backups"
