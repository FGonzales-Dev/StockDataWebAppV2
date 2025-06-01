# 🛩️ Stock Data Web App - Fly.io Deployment Guide

Deploy your Django stock scraper to Fly.io with **2GB RAM for just $3.88/month** - perfect for Chrome-based web scraping!

## 🚀 **Quick Start**

### 1. **Install Fly.io CLI**
```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2. **Login to Fly.io**
```bash
flyctl auth login
```

### 3. **Deploy with One Command**
```bash
chmod +x deploy-fly.sh
./deploy-fly.sh
```

## 📋 **Manual Deployment Steps**

### 1. **Create Fly.io App**
```bash
flyctl apps create stockdata-scraper --machines
```

### 2. **Set Environment Variables**
```bash
# Required secrets
flyctl secrets set SECRET_KEY="your-super-secret-django-key"

# Optional: External Redis for Celery
flyctl secrets set REDIS_URL="redis://your-redis-url:6379"

# Optional: External database (default uses SQLite)
flyctl secrets set DATABASE_URL="postgresql://user:pass@host:port/db"
```

### 3. **Deploy Application**
```bash
flyctl deploy
```

### 4. **Run Post-Deploy Commands**
```bash
# Database migrations
flyctl ssh console --command "python manage.py migrate"

# Collect static files
flyctl ssh console --command "python manage.py collectstatic --noinput"

# Create superuser
flyctl ssh console --command "python manage.py createsuperuser"
```

## 🛠️ **Configuration Details**

### **Memory & Performance**
- **2GB RAM** optimized for Chrome scraping
- **Shared CPU** for cost efficiency
- **Auto-scaling** disabled to maintain persistent tasks

### **Chrome Configuration**
- Optimized for Fly.io's 2GB memory limit
- Uses `--max_old_space_size=1024` for better performance
- Stable flags tested on Fly.io infrastructure

### **Health Checks**
- HTTP health check on `/health/` endpoint
- TCP checks for container health
- 30-second intervals with graceful startup

## 🔧 **Useful Commands**

```bash
# Check app status
flyctl status

# View real-time logs
flyctl logs

# SSH into your app
flyctl ssh console

# Scale your app (upgrade/downgrade)
flyctl scale memory 4096  # Upgrade to 4GB if needed

# Restart app
flyctl restart

# Destroy app (careful!)
flyctl apps destroy stockdata-scraper
```

## 📊 **Monitoring & Debugging**

### **View Logs**
```bash
# Real-time logs
flyctl logs

# Historical logs
flyctl logs --app stockdata-scraper

# Specific time range
flyctl logs --since="1h"
```

### **Check Resource Usage**
```bash
flyctl status
flyctl vm status
```

### **Debug Chrome Issues**
```bash
# SSH into app and test Chrome
flyctl ssh console
python test_stable_chrome.py
```

## 💰 **Cost Breakdown**

| Resource | Monthly Cost |
|----------|-------------|
| **2GB RAM Machine** | $3.88 |
| **Bandwidth** | ~$0.20 (typical) |
| **Storage** | ~$0.15 (1GB volume) |
| **Total** | **~$4.23/month** |

Compare to Railway Pro: $20/month for similar resources!

## 🚨 **Troubleshooting**

### **Chrome Memory Issues**
```bash
# Check memory usage
flyctl ssh console
htop

# Reduce Chrome memory usage
# Edit core/tasks.py and reduce --max_old_space_size=512
```

### **Database Issues**
```bash
# Check SQLite database
flyctl ssh console
ls -la /data/  # If using volumes
python manage.py dbshell
```

### **Celery Worker Issues**
```bash
# Check if Celery is running
flyctl ssh console
ps aux | grep celery

# Restart Celery worker manually
python manage.py celeryd -E --loglevel=info --concurrency=1
```

### **Static Files Not Loading**
```bash
# Re-collect static files
flyctl ssh console --command "python manage.py collectstatic --noinput --clear"
```

## 🔄 **Migration from Railway**

1. **Export data** from Railway (if any)
2. **Deploy to Fly.io** using this guide
3. **Import data** to Fly.io
4. **Test functionality** thoroughly
5. **Update DNS** (if using custom domain)
6. **Shut down Railway** app

## ⚡ **Performance Tips**

1. **Use Redis** for Celery if running many tasks:
   ```bash
   flyctl redis create
   ```

2. **Upgrade to 4GB** if needed:
   ```bash
   flyctl scale memory 4096
   ```

3. **Use persistent volumes** for large data:
   ```bash
   flyctl volumes create data_volume --size 10
   ```

4. **Monitor costs**:
   ```bash
   flyctl billing
   ```

## 🌐 **Custom Domain (Optional)**

```bash
# Add your domain
flyctl ips allocate-v4
flyctl ips allocate-v6

# Set up DNS
flyctl certs create yourdomain.com

# Update ALLOWED_HOSTS in settings.py
```

## 📞 **Support**

- **Fly.io Docs**: https://fly.io/docs/
- **Django on Fly.io**: https://fly.io/docs/django/
- **Community**: https://community.fly.io/

## 🎉 **Success!**

Your Stock Data Web App is now running on Fly.io with:
- ✅ **2GB RAM** for stable Chrome operation
- ✅ **~$4/month** cost (6x cheaper than alternatives)
- ✅ **Global edge deployment**
- ✅ **Automatic HTTPS**
- ✅ **Zero-downtime deployments**

Happy scraping! 🚀 