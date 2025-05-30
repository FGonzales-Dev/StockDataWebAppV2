#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_scraper.settings')
    django.setup()

def run_management_command(command_args, description):
    """Run a Django management command with error handling"""
    try:
        print(f"Running: {description}...")
        execute_from_command_line(command_args)
        print(f"✓ {description} completed successfully")
        return True
    except Exception as e:
        print(f"✗ Error during {description}: {str(e)}")
        return False

def start_server(port):
    """Start the server using gunicorn or fallback to runserver"""
    print("Setting up Django environment...")
    setup_django()
    
    print("Starting server...")
    try:
        import gunicorn.app.wsgiapp as wsgiapp
        from stock_scraper.wsgi import application
        
        print("Using Gunicorn server...")
        # Configure gunicorn
        sys.argv = ['gunicorn', 'stock_scraper.wsgi:application', 
                   '--bind', f'0.0.0.0:{port}', 
                   '--timeout', '600',
                   '--workers', '1',
                   '--log-level', 'info']
        wsgiapp.run()
    except ImportError as e:
        print(f"Gunicorn not available ({e}), using Django dev server...")
        execute_from_command_line(['manage.py', 'runserver', f'0.0.0.0:{port}'])
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Get port from environment
    port = os.environ.get('PORT', '8000')
    print(f"Starting deployment process...")
    print(f"Port: {port}")
    print(f"Python version: {sys.version}")
    
    # Run migrations
    if not run_management_command(['manage.py', 'migrate'], 'Database migrations'):
        print("Migration failed, but continuing...")
    
    # Collect static files
    if not run_management_command(['manage.py', 'collectstatic', '--noinput'], 'Static file collection'):
        print("Static file collection failed, but continuing...")
    
    # Start the server
    start_server(port) 