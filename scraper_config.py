# Scraper Configuration Settings
# =================================

# Browser Display Settings
# ========================
# Set to True to see the browser window during scraping (useful for debugging)
# Set to False to run in headless mode (faster, no GUI, good for production)
SHOW_BROWSER = False

# Debug Settings
# ==============
# Enable debug logging and file outputs
DEBUG_MODE = True

# Save screenshots when errors occur
SAVE_DEBUG_SCREENSHOTS = True

# Save page source when errors occur
SAVE_DEBUG_PAGE_SOURCE = True

# Timeout Settings
# ================
# How long to wait for elements to load (in seconds)
ELEMENT_WAIT_TIMEOUT = 30

# How long to wait for page to load (in seconds)
PAGE_LOAD_TIMEOUT = 30

# Performance Settings
# ===================
# Number of retry attempts for failed operations
MIN_RETRIES = 3
MAX_RETRIES = 5

# Delay between operations (in seconds)
MIN_OPERATION_DELAY = 5
MAX_OPERATION_DELAY = 7

# Browser Settings
# ================
# Window size for browser (when visible)
BROWSER_WIDTH = 1920
BROWSER_HEIGHT = 1080

# User agent string
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"

# Download Settings
# =================
# Directory for downloaded files (relative to BASE_DIR)
DOWNLOAD_DIRECTORY = "/selenium"

# File cleanup after processing
CLEANUP_TEMP_FILES = True 