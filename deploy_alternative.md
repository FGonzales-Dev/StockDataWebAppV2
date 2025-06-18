# Alternative DigitalOcean Deployment (Manual Configuration)

If the `app.yaml` file isn't being recognized, use this manual configuration in the DigitalOcean dashboard:

## 1. App Settings

**Source:**
- Repository: `your-username/StockDataWebAppV2`
- Branch: `digital-ocean-deployment-v2`

## 2. Web Service Configuration

**Resource:**
- Type: Web Service
- Source Directory: `/`
- Build Command: `pip install -r requirements.txt`
- Run Command: `gunicorn --bind 0.0.0.0:8080 stock_scraper.wsgi:application`

**Plan:**
- Instance Count: 1
- Instance Size: Basic (512 MB RAM, 1 vCPU)

## 3. Environment Variables

Set these in the DigitalOcean dashboard:

```
DEBUG=False
SECRET_KEY=your-generated-secret-key-here
ALLOWED_HOSTS=your-app-name.ondigitalocean.app
DJANGO_SETTINGS_MODULE=stock_scraper.settings
```

## 4. Database

**Add Component:**
- Type: Database
- Engine: PostgreSQL
- Version: 13
- Size: Development Database ($7/month)

## 5. Post-Deployment Commands

After the first successful deployment, run these commands in the console:

```bash
# Run migrations
python manage.py migrate --noinput

# Create superuser (optional)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## 6. Alternative Run Commands to Try

If the basic gunicorn command doesn't work, try these alternatives:

**Option 1 - With explicit settings:**
```
DJANGO_SETTINGS_MODULE=stock_scraper.settings gunicorn --bind 0.0.0.0:8080 stock_scraper.wsgi:application
```

**Option 2 - With worker options:**
```
gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 stock_scraper.wsgi:application
```

**Option 3 - Using Django's built-in server (for debugging only):**
```
python manage.py runserver 0.0.0.0:8080
```

## 7. Troubleshooting Steps

If you're still getting "No application module specified":

1. **Check the console logs** in DigitalOcean dashboard
2. **Verify Python path** - try this run command:
   ```
   python -c "import sys; print(sys.path)" && gunicorn --bind 0.0.0.0:8080 stock_scraper.wsgi:application
   ```
3. **Test WSGI import** - try this run command:
   ```
   python -c "from stock_scraper.wsgi import application; print('WSGI OK')" && gunicorn --bind 0.0.0.0:8080 stock_scraper.wsgi:application
   ```

## 8. Debug Commands

Use these commands in the DigitalOcean console to debug:

```bash
# Check if files are present
ls -la

# Check if Django can be imported
python -c "import django; print(django.get_version())"

# Check if settings module works
python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='stock_scraper.settings'; import django; django.setup(); print('Settings OK')"

# Check if WSGI application can be imported
python -c "from stock_scraper.wsgi import application; print('WSGI application found:', type(application))"

# Test gunicorn directly
gunicorn --check-config stock_scraper.wsgi:application
``` 