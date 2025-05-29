# Example Scraper Configuration Files
# ===================================

# DEBUGGING MODE - Use this when you want to see what's happening
# ================================================================
"""
# Copy this to scraper_config.py for debugging:

SHOW_BROWSER = True              # 👁️ Show browser window
DEBUG_MODE = True                # 🐛 Enable debug logging  
SAVE_DEBUG_SCREENSHOTS = True    # 📸 Save screenshots on errors
SAVE_DEBUG_PAGE_SOURCE = True    # 📄 Save page source on errors
ELEMENT_WAIT_TIMEOUT = 30        # ⏱️ Wait 30 seconds for elements
PAGE_LOAD_TIMEOUT = 60           # ⏱️ Wait 60 seconds for page loads
"""

# PRODUCTION MODE - Use this for fast, automated scraping
# =======================================================
"""
# Copy this to scraper_config.py for production:

SHOW_BROWSER = False             # 🔍 Hidden browser (headless)
DEBUG_MODE = False               # 🚀 Minimal logging
SAVE_DEBUG_SCREENSHOTS = False   # 💾 No screenshots (saves space)
SAVE_DEBUG_PAGE_SOURCE = False   # 💾 No page source (saves space)
ELEMENT_WAIT_TIMEOUT = 15        # ⚡ Faster timeouts
PAGE_LOAD_TIMEOUT = 30           # ⚡ Faster page loads
"""

# TESTING MODE - Use this for development testing
# ===============================================
"""
# Copy this to scraper_config.py for testing:

SHOW_BROWSER = True              # 👁️ Show browser window
DEBUG_MODE = True                # 🐛 Enable debug logging
SAVE_DEBUG_SCREENSHOTS = True    # 📸 Save screenshots on errors
SAVE_DEBUG_PAGE_SOURCE = False   # 💾 Skip page source (faster)
ELEMENT_WAIT_TIMEOUT = 45        # ⏱️ Longer waits for slow connections
PAGE_LOAD_TIMEOUT = 90           # ⏱️ Longer page load waits
""" 