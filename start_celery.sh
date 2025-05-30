#!/bin/bash

# Wait for database to be ready
python manage.py migrate

# Start Celery worker
exec celery -A stock_scraper worker --loglevel=info --concurrency=1 