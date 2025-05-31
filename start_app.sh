#!/bin/bash

echo "🚀 Starting Stock Data Web App..."

# Set environment variables
export RAILWAY_ENVIRONMENT=true
export CHROME_BIN=/usr/bin/google-chrome-stable
export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Ensure /tmp directory exists and is writable
mkdir -p /tmp
chmod 777 /tmp

echo "📊 Checking database setup..."

# Try to run migrations, but don't fail if they don't work
python manage.py migrate --noinput --run-syncdb 2>/dev/null || {
    echo "⚠️ Database migrations failed, but continuing..."
    
    # Try to create a simple SQLite database
    python -c "
import os
import sqlite3
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_scraper.settings')
django.setup()

try:
    # Create a simple database file
    db_path = '/tmp/db.sqlite3'
    conn = sqlite3.connect(db_path)
    conn.close()
    print('✅ SQLite database file created')
except Exception as e:
    print(f'❌ Failed to create database: {e}')
" || echo "Database creation also failed, but continuing..."
}

echo "🌐 Starting Gunicorn server..."

# Start the application
exec gunicorn stock_scraper.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120 