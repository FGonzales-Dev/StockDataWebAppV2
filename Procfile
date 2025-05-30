web: python manage.py migrate && gunicorn stock_scraper.wsgi --bind 0.0.0.0:$PORT --timeout 600 --log-file -

celery_worker: celery -A stock_scraper worker --loglevel=info
celery: celery -A stock_scraper worker --loglevel=info 

