# Install Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Check Chrome installation path
RUN echo "Chrome path: $(which google-chrome-stable)" \
    && google-chrome-stable --version

# Install ChromeDriver 