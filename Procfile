web: gunicorn cb_dj_weather_app.wsgi --timeout 600 --log-file -



celery: celery -A cb_dj_weather_app worker --beat  --concurrency 2