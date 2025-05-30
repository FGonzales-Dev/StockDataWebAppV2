web: python manage.py collectstatic --noinput && python manage.py migrate && gunicorn stock_scraper.wsgi --timeout 600

celery_worker: celery -A stock_scraper worker --loglevel=info
celery: celery -A stock_scraper worker --loglevel=info 

