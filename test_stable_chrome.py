#!/usr/bin/env python3
"""
Test script for stable Chrome configuration
Run this to test if Chrome works with the new stable settings
"""

import os
import sys
import time
from selenium import webdriver
import undetected_chromedriver as uc

def test_stable_chrome():
    """Test the stable Chrome configuration"""
    print("🧪 Testing stable Chrome configuration...")
    
    # Check if running on Railway
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("CHROME_BIN")
    print(f"🚂 Railway environment detected: {is_railway}")
    
    # STABLE Chrome options - only essential flags
    options = uc.ChromeOptions()
    
    # Core stability flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    
    if is_railway:
        print("🚂 Adding Railway-optimized Chrome options...")
        
        # Essential Railway flags only
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--remote-debugging-port=9222")
        
        # Conservative memory management
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=512")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        
        # Disable unnecessary features (safe removals)
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-notifications")
        options.add_argument("--mute-audio")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        
        # Performance optimizations (proven stable)
        options.add_argument("--disable-features=VizDisplayCompositor,TranslateUI")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-infobars")
        
        # Set binary location
        chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome-stable")
        if os.path.exists(chrome_bin):
            options.binary_location = chrome_bin
            print(f"🔧 Chrome binary: {chrome_bin}")
    
    # User agent
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    
    # Window size
    options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        print("🚀 Creating Chrome driver...")
        
        # Handle Railway binary location
        if is_railway:
            chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome-stable")
            if os.path.exists(chrome_bin):
                driver = uc.Chrome(options=options, browser_executable_path=chrome_bin)
            else:
                driver = uc.Chrome(options=options)
        else:
            driver = uc.Chrome(options=options)
        
        print("✅ Chrome driver created successfully!")
        
        # Test basic functionality
        print("🧪 Testing basic navigation...")
        driver.get("about:blank")
        print("✅ Basic navigation successful!")
        
        # Test with a simple page
        print("🧪 Testing with example.com...")
        driver.get("https://example.com")
        time.sleep(2)
        
        title = driver.title
        print(f"✅ Page loaded successfully! Title: {title}")
        
        # Test JavaScript execution
        print("🧪 Testing JavaScript execution...")
        ready_state = driver.execute_script("return document.readyState")
        print(f"✅ JavaScript working! Ready state: {ready_state}")
        
        print("🎉 All tests passed! Chrome configuration is stable.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
        
    finally:
        if driver:
            try:
                driver.quit()
                print("🔄 Chrome driver closed successfully")
            except Exception as e:
                print(f"⚠️ Error closing driver: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 STABLE CHROME CONFIGURATION TEST")
    print("=" * 50)
    
    success = test_stable_chrome()
    
    print("=" * 50)
    if success:
        print("✅ TEST RESULT: SUCCESS")
        print("🎯 Chrome configuration is stable and ready for scraping!")
        sys.exit(0)
    else:
        print("❌ TEST RESULT: FAILED")
        print("🔧 Chrome configuration needs further adjustment")
        sys.exit(1) 