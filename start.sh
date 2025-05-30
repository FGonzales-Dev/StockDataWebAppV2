#!/bin/bash
set -e

echo "Python version:"
python --version

echo "Pip list (showing gunicorn):"
python -m pip list | grep -i gunicorn || echo "Gunicorn not found in pip list"

echo "Checking if gunicorn is in PATH:"
which gunicorn || echo "gunicorn not in PATH, using python -m gunicorn"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate

echo "Starting gunicorn server..."
if command -v gunicorn &> /dev/null; then
    gunicorn stock_scraper.wsgi --timeout 600 --bind 0.0.0.0:${PORT:-8000}
else
    python -m gunicorn stock_scraper.wsgi --timeout 600 --bind 0.0.0.0:${PORT:-8000}
fi 