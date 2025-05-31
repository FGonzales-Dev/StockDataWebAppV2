#!/bin/bash

echo "🚀 Starting Stock Data Web App on Railway Hobby Plan..."

# Railway Hobby Plan optimization (512MB-1GB memory limit)
export MALLOC_ARENA_MAX=1
export PYTHONUNBUFFERED=1
export NODE_OPTIONS="--max-old-space-size=256"

# Chrome environment optimization for Railway Hobby Plan
export CHROME_BIN="/usr/bin/google-chrome-stable"
export CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
export CHROME_FLAGS="--memory-pressure-off --disable-features=VizDisplayCompositor --single-process --max_old_space_size=256"

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

echo "🌐 Starting Gunicorn server for Hobby Plan..."

# Ultra-optimized Gunicorn configuration for Railway Hobby Plan
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 1 \
    --timeout 90 \
    --max-requests 25 \
    --max-requests-jitter 5 \
    --worker-class sync \
    stock_scraper.wsgi:application 