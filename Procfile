web: python -m pip list | grep gunicorn && python manage.py collectstatic --noinput && python manage.py migrate && python -m gunicorn stock_scraper.wsgi --timeout 600 --bind 0.0.0.0:$PORT

celery_worker: celery -A stock_scraper worker --loglevel=info
celery: celery -A stock_scraper worker --loglevel=info 

