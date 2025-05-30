web: gunicorn stock_scraper.wsgi --timeout 600 --log-file -

celery_worker: celery -A stock_scraper worker --loglevel=info
celery: celery -A stock_scraper worker --loglevel=info 

