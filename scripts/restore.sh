#!/bin/bash

# MaskGate Database Restore Script
# This script restores a database from a backup

set -e

echo "🔄 Restoring database from backup..."

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

# List available backups
BACKUP_DIR="../backups"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ No backups directory found"
    exit 1
fi

echo "📁 Available backups:"
ls -lh "$BACKUP_DIR"/maskgate_backup_*.sql.gz 2>/dev/null || echo "No backups found"

# Ask which backup to restore
read -p "Enter backup filename to restore (or 'cancel' to abort): " BACKUP_FILE

if [ "$BACKUP_FILE" = "cancel" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Confirm restore
read -p "⚠️  This will replace the current database. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 0
fi

# Drop existing database
echo "🗑️  Dropping existing database..."
dropdb -U "$DB_USER" "$DB_NAME" || echo "Database may not exist"

# Create new database
echo "🆕 Creating new database..."
createdb -U "$DB_USER" "$DB_NAME"

# Decompress and restore
echo "📦 Restoring from backup..."
gunzip -c "$BACKUP_DIR/$BACKUP_FILE" | psql -U "$DB_USER" -d "$DB_NAME"

echo "✅ Restore complete!"
echo "🗄️  Database $DB_NAME has been restored from $BACKUP_FILE"
