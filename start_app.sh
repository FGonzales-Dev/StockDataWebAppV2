#!/bin/bash

echo "🚀 Starting Stock Data Web App..."

# Railway environment optimization
export MALLOC_ARENA_MAX=2
export PYTHONUNBUFFERED=1

# Chrome environment optimization for Railway
export CHROME_BIN="/usr/bin/google-chrome-stable"
export CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
export CHROME_FLAGS="--memory-pressure-off --disable-features=VizDisplayCompositor --single-process"

# Create necessary directories
mkdir -p selenium
mkdir -p drivers

echo "📊 Checking database setup..."

# Try database migrations with fallback
python manage.py migrate --noinput 2>/dev/null || {
    echo "⚠️ Database migrations failed, but continuing..."
}

# Ensure SQLite database exists
python -c "
import os
import sqlite3
db_path = 'db.sqlite3'
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.close()
    print('✅ SQLite database file created')
else:
    print('✅ SQLite database exists')
" 2>/dev/null || echo "⚠️ Database check failed"

echo "🌐 Starting Gunicorn server..."

# Optimized Gunicorn configuration for Railway
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 2 \
    --timeout 120 \
    --max-requests 100 \
    --max-requests-jitter 10 \
    stock_scraper.wsgi:application 