#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_scraper.settings')
    
    # Get port from environment
    port = os.environ.get('PORT', '8000')
    
    # Run migrations
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Collect static files
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    # Try to use gunicorn, fall back to runserver
    try:
        import gunicorn.app.wsgiapp as wsgiapp
        from stock_scraper.wsgi import application
        
        # Configure gunicorn
        sys.argv = ['gunicorn', 'stock_scraper.wsgi:application', 
                   '--bind', f'0.0.0.0:{port}', '--timeout', '600']
        wsgiapp.run()
    except ImportError:
        # Fallback to Django dev server
        execute_from_command_line(['manage.py', 'runserver', f'0.0.0.0:{port}']) 