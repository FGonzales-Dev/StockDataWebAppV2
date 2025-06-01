#!/bin/bash

echo "🛩️ Deploying Stock Data Web App to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Installing..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "🔑 Please log in to Fly.io:"
    flyctl auth login
fi

# Create app if it doesn't exist
if ! flyctl apps list | grep -q "stockdata-scraper"; then
    echo "🏗️ Creating new Fly.io app..."
    flyctl apps create stockdata-scraper --machines
else
    echo "✅ App 'stockdata-scraper' already exists"
fi

# Set secrets (you'll need to set these)
echo "🔐 Setting up secrets..."
echo "Please set your secrets using:"
echo "flyctl secrets set SECRET_KEY=your-secret-key"
echo "flyctl secrets set REDIS_URL=your-redis-url"
echo "flyctl secrets set DATABASE_URL=your-database-url (optional)"
echo ""
echo "Press Enter when you've set your secrets..."
read

# Create volume for SQLite database (if not using external DB)
if ! flyctl volumes list | grep -q "stockdata_db"; then
    echo "💾 Creating persistent volume for database..."
    flyctl volumes create stockdata_db --size 1 --region sjc
fi

# Deploy the application
echo "🚀 Deploying to Fly.io..."
flyctl deploy --strategy immediate

# Run database migrations
echo "🗃️ Running database migrations..."
flyctl ssh console --command "python manage.py migrate"

# Collect static files
echo "📁 Collecting static files..."
flyctl ssh console --command "python manage.py collectstatic --noinput"

# Create superuser (optional)
echo "👤 Do you want to create a superuser? (y/n)"
read -r create_superuser
if [[ $create_superuser == "y" ]]; then
    flyctl ssh console --command "python manage.py createsuperuser"
fi

# Show deployment info
echo "✅ Deployment completed!"
echo "🌐 Your app is available at: https://stockdata-scraper.fly.dev"
echo "📊 Monitor your app: flyctl status"
echo "📝 View logs: flyctl logs"
echo "🔧 SSH into app: flyctl ssh console"

echo "🎉 Stock Data Web App successfully deployed to Fly.io!" 