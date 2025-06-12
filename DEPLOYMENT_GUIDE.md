# Stock Scraper Deployment Guide

This guide covers deploying your stock scraper application to various platforms after removing Fly.io dependencies.

## 🚀 Quick Deployment Options

### Option 1: DigitalOcean Droplet (Recommended)

**Cost**: $6-12/month | **Setup Time**: 30 minutes

#### Step 1: Create Droplet
1. Create DigitalOcean account
2. Create new droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Size**: Basic plan, 1GB RAM ($6/month)
   - **Region**: Choose closest to your location

#### Step 2: Setup Server
```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose -y

# Create app directory
mkdir /app && cd /app
```

#### Step 3: Deploy Application
```bash
# Clone your repository
git clone YOUR_REPOSITORY_URL .

# Set environment variables
export SECRET_KEY="your-secret-key-here"

# Deploy with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
```

#### Step 4: Configure Domain (Optional)
```bash
# Install nginx for reverse proxy
apt install nginx -y

# Configure nginx (create /etc/nginx/sites-available/stockscraper)
server {
    listen 80;
    server_name YOUR_DOMAIN.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
ln -s /etc/nginx/sites-available/stockscraper /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### Option 2: Railway

**Cost**: $5/month | **Setup Time**: 10 minutes

1. Connect GitHub repository to Railway
2. Add environment variables:
   - `PRODUCTION=true`
   - `SECRET_KEY=your-secret-key`
3. Deploy automatically

### Option 3: Render

**Cost**: $7/month | **Setup Time**: 15 minutes

1. Connect GitHub repository
2. Configure as Web Service
3. Add environment variables
4. Deploy

## 🔧 Configuration Updates Needed

### 1. Update Domain References

Replace `YOUR_DOMAIN_HERE` in these files with your actual domain:
- `improved_google_apps_script.js`
- Documentation files (*.md)

### 2. Environment Variables

Set these environment variables on your platform:
```bash
PRODUCTION=true
SECRET_KEY=your-django-secret-key
REDIS_URL=redis://localhost:6379  # (if not using Docker Compose)
```

### 3. Django Settings

Update `ALLOWED_HOSTS` in `stock_scraper/settings.py`:
```python
ALLOWED_HOSTS = [
    '0.0.0.0',
    '127.0.0.1',
    'localhost',
    'YOUR_DOMAIN.com',  # Add your domain
    'YOUR_DROPLET_IP',  # Add your server IP
]
```

## 📊 Resource Requirements

Based on your monitoring data:

| Usage Level | RAM Needed | Recommended Server |
|-------------|------------|-------------------|
| Light (< 256MB peak) | 512MB | DigitalOcean $6/month |
| Moderate (< 512MB peak) | 1GB | DigitalOcean $12/month |
| Heavy (< 1GB peak) | 2GB | DigitalOcean $24/month |

## 🔍 Monitoring

Your application includes built-in monitoring at `/monitoring/dashboard/`

Access it at: `http://YOUR_DOMAIN/monitoring/dashboard/`

## 🛠️ Maintenance Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update application
git pull
docker-compose build
docker-compose up -d

# Backup database
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)
```

## 🚨 Troubleshooting

### Common Issues:

1. **Chrome/Selenium Issues**
   ```bash
   # Check if Chrome is working
   docker-compose exec web google-chrome --version
   ```

2. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats
   ```

3. **Database Issues**
   ```bash
   # Run migrations
   docker-compose exec web python manage.py migrate
   ```

## 💰 Cost Comparison

| Platform | Monthly Cost | Pros | Cons |
|----------|-------------|------|------|
| DigitalOcean | $6-24 | Full control, scalable | Requires setup |
| Railway | $5 | Easy setup | Memory limits |
| Render | $7-25 | Good balance | More expensive |
| Heroku | $7+ | Very easy | Most expensive |

## 🎯 Recommended Setup

For your stock scraper, we recommend:
- **DigitalOcean Droplet** (1GB RAM, $12/month)
- **Docker Compose** deployment
- **Nginx** reverse proxy
- **Automated backups**

This gives you the best balance of cost, performance, and control. 