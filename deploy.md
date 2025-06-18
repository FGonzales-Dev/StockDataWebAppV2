# DigitalOcean App Platform Deployment Guide

This document outlines the steps to deploy your Stock Data Web App to DigitalOcean App Platform.

## Prerequisites

1. GitHub repository with your code
2. DigitalOcean account
3. Firebase/Firestore service account key (if using Firebase features)

## Pre-Deployment Steps

### 1. Update Repository Information

1. Edit `.digitalocean/app.yaml` and replace:
   - `your-username/StockDataWebAppV2` with your actual GitHub repository
   - `your-app-name.ondigitalocean.app` with your desired app name

### 2. Environment Variables

The following environment variables need to be configured in DigitalOcean:

**Required:**
- `SECRET_KEY`: Generate a new Django secret key
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Your DigitalOcean app URL
- `DATABASE_URL`: Will be auto-configured by DigitalOcean PostgreSQL
- `REDIS_URL`: Will be auto-configured by DigitalOcean Redis

**Optional (if using Firebase):**
- `GOOGLE_APPLICATION_CREDENTIALS`: Base64 encoded service account key

### 3. Generate a New Secret Key

Run this command to generate a new Django secret key:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## Deployment Steps

### 1. Connect to DigitalOcean

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Choose "GitHub" as your source
4. Select your repository and branch (`digital-ocean-deployment-v2`)

### 2. Configure App Settings

1. DigitalOcean will automatically detect the `app.yaml` configuration
2. Review the detected configuration:
   - Web service running on Python
   - PostgreSQL database
   - Redis for Celery
   - Celery worker and beat processes

### 3. Set Environment Variables

In the DigitalOcean dashboard, configure these environment variables:

```
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app-name.ondigitalocean.app
DJANGO_SETTINGS_MODULE=stock_scraper.settings
```

### 4. Deploy

1. Click "Create Resources"
2. Wait for the deployment to complete
3. Your app will be available at `https://your-app-name.ondigitalocean.app`

## Post-Deployment

### 1. Run Database Migrations

After the first deployment, you may need to run migrations manually:

1. Go to the App Platform console
2. Open a console for your web service
3. Run: `python manage.py migrate`
4. Create a superuser: `python manage.py createsuperuser`

### 2. Collect Static Files

Static files should be collected automatically, but if needed:
```bash
python manage.py collectstatic --noinput
```

## Important Notes

1. **Database**: PostgreSQL is configured automatically by DigitalOcean
2. **Redis**: Redis is configured for Celery task queuing
3. **Static Files**: Handled by WhiteNoise middleware
4. **Celery**: Background task processing is enabled with worker and beat processes
5. **Security**: Production security settings are enabled when `DEBUG=False`

## Troubleshooting

### Common Issues

1. **Static Files Not Loading**: Ensure `STATICFILES_STORAGE` is set correctly
2. **Database Connection Issues**: Check `DATABASE_URL` environment variable
3. **Celery Not Working**: Verify Redis connection and worker processes are running
4. **Firebase Issues**: Ensure service account key is properly configured

### Logs

Check application logs in the DigitalOcean App Platform dashboard:
- Go to your app
- Click on "Runtime Logs"
- Select the service (web, worker, or beat)

## Cost Optimization

- Start with `basic-xxs` instances and scale up as needed
- Consider using development databases for testing
- Monitor resource usage in the DigitalOcean dashboard

## Security Considerations

1. Never commit sensitive data to your repository
2. Use environment variables for all secrets
3. Regularly rotate your SECRET_KEY
4. Keep dependencies updated
5. Monitor security advisories for your packages 