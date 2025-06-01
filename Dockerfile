# Fly.io optimized Dockerfile for Stock Data Web App
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/google-chrome-stable
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV DISPLAY=:99
ENV FLY_ENVIRONMENT=true

# Fly.io memory optimization
ENV MALLOC_ARENA_MAX=2
ENV NODE_OPTIONS="--max-old-space-size=512"

# Set work directory
WORKDIR /app

# Install system dependencies optimized for Fly.io
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    curl \
    libpq-dev \
    gcc \
    python3-dev \
    # Chrome dependencies for Ubuntu/Debian
    fonts-liberation \
    libasound2t64 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libnss3 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome with fixed version for Fly.io stability
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver with version matching Chrome
RUN CHROME_VERSION=$(google-chrome --version | cut -d' ' -f3 | cut -d'.' -f1-3) \
    && echo "Chrome version: $CHROME_VERSION" \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip" -O chromedriver.zip \
    && unzip -q chromedriver.zip \
    && cp chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf chromedriver.zip chromedriver-linux64 \
    && chromedriver --version

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p selenium drivers static

# Collect static files
RUN python manage.py collectstatic --noinput

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' flyuser \
    && chown -R flyuser:flyuser /app
USER flyuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden by fly.toml)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "--timeout", "120", "stock_scraper.wsgi:application"] 