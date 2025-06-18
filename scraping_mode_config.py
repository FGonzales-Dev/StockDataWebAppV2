# Scraping Mode Configuration
# =========================

# Set this to control scraping behavior:
# - 'auto': Automatically detect Redis/Celery availability (recommended)
# - 'direct': Always use direct/synchronous scraping
# - 'background': Always try to use Redis/Celery (will fail if not available)

SCRAPING_MODE = 'direct'

# You can change this to:
# SCRAPING_MODE = 'auto'     # Auto-detect Redis/Celery
# SCRAPING_MODE = 'background'  # Force background tasks

# Redis/Celery Configuration (used when available)
USE_REDIS_WHEN_AVAILABLE = True
REDIS_FALLBACK_TO_DIRECT = True  # If Redis fails, fall back to direct

# Direct Mode Settings
DIRECT_MODE_SHOW_PROGRESS = True  # Show immediate results in direct mode
DIRECT_MODE_TIMEOUT = 300  # 5 minutes timeout for direct scraping 