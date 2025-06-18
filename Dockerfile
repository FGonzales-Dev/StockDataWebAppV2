# Install Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Check Chrome installation path and version
RUN echo "Chrome path: $(which google-chrome-stable)" \
    && echo "Chrome version: $(google-chrome-stable --version)"

# Install ChromeDriver with a compatible version
RUN CHROME_VERSION=$(google-chrome-stable --version | awk '{print $3}') \
    && CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d'.' -f1) \
    && CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_MAJOR_VERSION) \
    && echo "Installing ChromeDriver version: $CHROME_DRIVER_VERSION for Chrome version: $CHROME_VERSION" \
    && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip \
    && echo "ChromeDriver path: $(which chromedriver)" \
    && chromedriver --version

# Set work directory 