#!/usr/bin/env python
"""
Production startup script for Railway deployment
Handles migrations, static files, and server startup with proper error handling
"""
import os
import sys
import subprocess
import time
import django
from django.core.management import execute_from_command_line

def run_command(command, description):
    """Run a command with error handling and logging"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_scraper.settings')
    django.setup()

def main():
    print("🎯 Starting Railway production deployment...")
    print(f"Python version: {sys.version}")
    print(f"PORT: {os.environ.get('PORT', 'Not set')}")
    print(f"DATABASE_URL: {'Set' if os.environ.get('DATABASE_URL') else 'Not set'}")
    print(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'Not set')}")
    
    # Setup Django
    print("🔧 Setting up Django environment...")
    setup_django()
    
    # Run migrations (non-blocking if fails)
    if not run_command("python manage.py migrate --noinput --verbosity 1", "Database migrations"):
        print("⚠️ Migrations failed, but continuing...")
    
    # Collect static files (non-blocking if fails)
    if not run_command("python manage.py collectstatic --noinput --clear --verbosity 1", "Static file collection"):
        print("⚠️ Static file collection failed, but continuing...")
    
    # Test Django setup
    print("🧪 Testing Django configuration...")
    try:
        from django.conf import settings
        from django.core.checks import run_checks
        
        # Run basic checks
        errors = run_checks(include_deployment_checks=False)
        if errors:
            print(f"⚠️ Django configuration warnings: {len(errors)} issues found")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
        else:
            print("✅ Django configuration looks good")
            
    except Exception as e:
        print(f"❌ Django configuration test failed: {e}")
        return False
    
    # Start the server
    port = os.environ.get('PORT', '8000')
    print(f"🌐 Starting Gunicorn server on port {port}...")
    
    gunicorn_cmd = [
        "gunicorn",
        "stock_scraper.wsgi:application",
        f"--bind=0.0.0.0:{port}",
        "--timeout=120",
        "--workers=2",
        "--max-requests=1000",
        "--preload",
        "--log-level=info",
        "--access-logfile=-",
        "--error-logfile=-"
    ]
    
    try:
        print(f"🚀 Executing: {' '.join(gunicorn_cmd)}")
        os.execvp("gunicorn", gunicorn_cmd)
    except Exception as e:
        print(f"❌ Failed to start Gunicorn: {e}")
        return False

if __name__ == '__main__':
    main() 