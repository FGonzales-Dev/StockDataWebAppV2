# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/google-chrome-stable
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV DISPLAY=:99
ENV RAILWAY_ENVIRONMENT=true

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    curl \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install Chrome dependencies (Debian/Ubuntu compatible packages)
RUN apt-get install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libnss3 \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+' | head -1) \
    && echo "Detected Chrome major version: $CHROME_VERSION" \
    && if [ -n "$CHROME_VERSION" ] && [ "$CHROME_VERSION" -ge 115 ]; then \
        echo "Using Chrome for Testing API for version $CHROME_VERSION"; \
        CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$CHROME_VERSION" 2>/dev/null); \
        if [ -n "$CHROMEDRIVER_VERSION" ] && [ "$CHROMEDRIVER_VERSION" != "Not Found" ]; then \
            echo "Downloading ChromeDriver $CHROMEDRIVER_VERSION"; \
            wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" -O chromedriver.zip; \
        else \
            echo "Chrome for Testing failed, using fixed version"; \
            wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/131.0.6778.108/linux64/chromedriver-linux64.zip" -O chromedriver.zip; \
        fi; \
    else \
        echo "Using legacy ChromeDriver for older Chrome"; \
        wget -q "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" -O chromedriver.zip; \
    fi \
    && unzip -q chromedriver.zip \
    && if [ -d chromedriver-linux64 ]; then \
        cp chromedriver-linux64/chromedriver /usr/local/bin/; \
    else \
        cp chromedriver /usr/local/bin/; \
    fi \
    && chmod +x /usr/local/bin/chromedriver \
    && ln -sf /usr/local/bin/chromedriver /usr/bin/chromedriver \
    && rm -f chromedriver.zip \
    && rm -rf chromedriver-linux64

# Verify installations
RUN google-chrome --version && /usr/local/bin/chromedriver --version

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . .

# Create selenium directory
RUN mkdir -p /app/selenium

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Start command
CMD ["gunicorn", "stock_scraper.wsgi:application", "--bind", "0.0.0.0:8000"] 