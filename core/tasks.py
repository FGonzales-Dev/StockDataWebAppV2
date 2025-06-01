import json
from celery import shared_task
from celery_progress.backend import ProgressRecorder

from django.http import HttpResponse

import os
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from stock_scraper.settings import BASE_DIR
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from time import sleep
import glob

import undetected_chromedriver as uc
import random


import pyrebase
import os
from multiprocessing.pool import ThreadPool
from functools import partial

import time
import threading
from django.core.cache import cache

# Import scraper configuration
try:
    from scraper_config import *
except ImportError:
    # Fallback defaults if config file doesn't exist
    SHOW_BROWSER = False
    DEBUG_MODE = False
    SAVE_DEBUG_SCREENSHOTS = False
    SAVE_DEBUG_PAGE_SOURCE = False
    ELEMENT_WAIT_TIMEOUT = 30
    PAGE_LOAD_TIMEOUT = 60
    BROWSER_WIDTH = 1920
    BROWSER_HEIGHT = 1080
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    DOWNLOAD_DIRECTORY = "/selenium"

config = {
    "apiKey": "AIzaSyD7fxurFiXK0agVyqr1wnfhnymIRCRiPXY",
    "authDomain": "scraper-b0a07.firebaseapp.com",
    "projectId": "scraper-b0a07",
    "storageBucket": "scraper-b0a07.appspot.com",
    "messagingSenderId": "1066439876574",
    "appId": "1:1066439876574:web:d0d4366594823a2d7f874f",
    "measurementId": "G-TJTZ8ZT9CW",
    "databaseURL": "https://scraper-b0a07-default-rtdb.asia-southeast1.firebasedatabase.app"

}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
database =firebase.database()

# Global Chrome session lock to prevent concurrent sessions
chrome_session_lock = threading.Lock()

def get_chrome_for_testing_driver():
    """
    Download ChromeDriver using the new Chrome for Testing API
    This replaces WebDriverManager with the official Chrome for Testing endpoints
    """
    import requests
    import zipfile
    import tempfile
    import platform
    import subprocess
    
    print("🔍 Starting Chrome for Testing driver download process...")
    
    try:
        # Detect Chrome installation based on environment
        chrome_candidates = []
        
        if os.environ.get("CHROME_BIN"):
            # Production environment (Railway)
            chrome_candidates.append(os.environ.get("CHROME_BIN"))
            print(f"💼 Production environment detected, Chrome binary: {os.environ.get('CHROME_BIN')}")
        
        # Add platform-specific Chrome paths
        system = platform.system().lower()
        print(f"🖥️ Detected platform: {system}")
        
        if system == "darwin":  # macOS
            chrome_candidates.extend([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "google-chrome",
                "chromium"
            ])
        elif system == "linux":  # Linux/Railway
            chrome_candidates.extend([
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "google-chrome-stable", 
                "google-chrome",
                "chromium-browser",
                "chromium"
            ])
        elif system == "windows":  # Windows
            chrome_candidates.extend([
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                "google-chrome",
                "chrome"
            ])
        
        print(f"🔍 Searching for Chrome in {len(chrome_candidates)} locations...")
        
        # Find working Chrome executable
        chrome_bin = None
        for i, candidate in enumerate(chrome_candidates):
            try:
                print(f"   Trying {i+1}/{len(chrome_candidates)}: {candidate}")
                # Test if this Chrome path works
                result = subprocess.run([candidate, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    chrome_bin = candidate
                    print(f"✅ Found Chrome at: {chrome_bin}")
                    print(f"   Version output: {result.stdout.strip()}")
                    break
                else:
                    print(f"   ❌ Failed with return code: {result.returncode}")
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
                print(f"   ❌ Error: {type(e).__name__}: {e}")
                continue
        
        if not chrome_bin:
            error_msg = f"No Chrome installation found. Tried {len(chrome_candidates)} locations."
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Get Chrome version
        print("🔍 Getting Chrome version...")
        result = subprocess.run([chrome_bin, "--version"], capture_output=True, text=True)
        chrome_version = result.stdout.strip().split()[-1]
        print(f"✅ Detected Chrome version: {chrome_version}")
        
        # Determine platform for download
        machine = platform.machine().lower()
        print(f"🔍 Machine architecture: {machine}")
        
        if system == "linux":
            if "arm" in machine or "aarch64" in machine:
                platform_name = "linux64"  # No ARM builds available, use x64
                print("⚠️ ARM detected, using linux64 (x64 emulation)")
            else:
                platform_name = "linux64"
                print("✅ Using linux64 platform")
        elif system == "darwin":
            if "arm" in machine or machine == "arm64":
                platform_name = "mac-arm64"
                print("✅ Using mac-arm64 platform")
            else:
                platform_name = "mac-x64"
                print("✅ Using mac-x64 platform")
        elif system == "windows":
            platform_name = "win64" if "64" in machine else "win32"
            print(f"✅ Using {platform_name} platform")
        else:
            platform_name = "linux64"  # Default fallback
            print(f"⚠️ Unknown system {system}, defaulting to linux64")
        
        # Download URL using Chrome for Testing API
        url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/{platform_name}/chromedriver-{platform_name}.zip"
        print(f"📥 Download URL: {url}")
        
        # Download ChromeDriver
        print("📥 Downloading ChromeDriver...")
        try:
            response = requests.get(url, timeout=30)
            print(f"📡 HTTP Response: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"Failed to download ChromeDriver: HTTP {response.status_code}"
                print(f"❌ {error_msg}")
                print(f"   Response text: {response.text[:200]}...")
                raise Exception(error_msg)
            
            print(f"✅ Download successful, content length: {len(response.content)} bytes")
            
        except requests.RequestException as e:
            error_msg = f"Network error downloading ChromeDriver: {e}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Extract to temporary directory
        print("📦 Extracting ChromeDriver...")
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "chromedriver.zip")
                print(f"   Temporary directory: {temp_dir}")
                
                with open(zip_path, "wb") as f:
                    f.write(response.content)
                print(f"   Zip file written: {zip_path}")
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    print(f"   Archive extracted, contents: {os.listdir(temp_dir)}")
                
                # Find the chromedriver executable
                chromedriver_name = "chromedriver.exe" if system == "windows" else "chromedriver"
                print(f"   Looking for executable: {chromedriver_name}")
                
                # Look for chromedriver in extracted directories
                found_driver = False
                for root, dirs, files in os.walk(temp_dir):
                    print(f"   Checking directory: {root}")
                    print(f"     Files: {files}")
                    
                    if chromedriver_name in files:
                        src_path = os.path.join(root, chromedriver_name)
                        print(f"   ✅ Found ChromeDriver at: {src_path}")
                        
                        # Copy to a permanent location
                        dest_dir = BASE_DIR / "drivers"
                        dest_dir.mkdir(exist_ok=True)
                        dest_path = dest_dir / chromedriver_name
                        
                        import shutil
                        shutil.copy2(src_path, dest_path)
                        os.chmod(dest_path, 0o755)
                        
                        # Verify the copied file
                        if os.path.exists(dest_path):
                            print(f"✅ ChromeDriver installed to: {dest_path}")
                            print(f"   File size: {os.path.getsize(dest_path)} bytes")
                            print(f"   Permissions: {oct(os.stat(dest_path).st_mode)[-3:]}")
                            return str(dest_path)
                        else:
                            print(f"❌ Failed to copy ChromeDriver to {dest_path}")
                            
                        found_driver = True
                        break
                
                if not found_driver:
                    error_msg = "ChromeDriver executable not found in downloaded archive"
                    print(f"❌ {error_msg}")
                    # Print full directory structure for debugging
                    for root, dirs, files in os.walk(temp_dir):
                        print(f"   {root}: {files}")
                    raise Exception(error_msg)
                    
        except Exception as e:
            error_msg = f"Error extracting ChromeDriver: {e}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
    except Exception as e:
        print(f"❌ Chrome for Testing download failed: {e}")
        return None


def get_chrome_driver(chrome_options=None):
    """
    Create ChromeDriver with stable configuration for Railway deployment.
    Uses reliable methods and stable Chrome flags.
    """
    print("🚀 Creating stable ChromeDriver...")
    
    # Check if running on Railway
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("CHROME_BIN")
    print(f"🚂 Railway environment detected: {is_railway}")
    
    # Create chrome options if not provided
    if chrome_options is None:
        chrome_options = webdriver.ChromeOptions()
        
        # Download preferences
        prefs = {'download.default_directory': str(BASE_DIR / "selenium")}
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Core stability flags
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        
        # Railway specific flags (stable only)
        if is_railway:
            chrome_options.add_argument("--headless")  # Force headless on Railway
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-gpu-sandbox")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Conservative memory management
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=512")
        
        # Window size and user agent
        chrome_options.add_argument(f"--window-size={BROWSER_WIDTH},{BROWSER_HEIGHT}")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")
        
        # Headless mode (force on Railway)
        if not SHOW_BROWSER or is_railway:
            chrome_options.add_argument("--headless")
            print("🔍 Running in HEADLESS mode")
        else:
            chrome_options.add_argument("--start-maximized")
            print("👁️ Running in VISIBLE mode")
    
    # Set Chrome binary location
    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin and os.path.exists(chrome_bin):
        chrome_options.binary_location = chrome_bin
        print(f"🏗️ Chrome binary: {chrome_bin}")
    elif is_railway:
        # Try alternative Chrome paths on Railway
        alternatives = ["/usr/bin/google-chrome-stable", "/usr/bin/google-chrome", "/usr/bin/chromium-browser"]
        for alt in alternatives:
            if os.path.exists(alt):
                chrome_options.binary_location = alt
                print(f"🏗️ Chrome binary (alternative): {alt}")
                break

    # Method 1: Railway system ChromeDriver (RAILWAY SPECIFIC)
    if is_railway:
        try:
            print("🚂 Method 1: Railway system ChromeDriver...")
            from selenium.webdriver.chrome.service import Service
            
            # Try multiple ChromeDriver locations
            chromedriver_paths = [
                os.environ.get("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver"),
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver",
                "/app/drivers/chromedriver"
            ]
            
            for chromedriver_path in chromedriver_paths:
                if chromedriver_path and os.path.exists(chromedriver_path):
                    print(f"🎯 Found ChromeDriver at: {chromedriver_path}")
                    service = Service(executable_path=chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    print(f"✅ SUCCESS: Railway system ChromeDriver at {chromedriver_path}")
                    return driver
                else:
                    print(f"❌ ChromeDriver not found at {chromedriver_path}")
            
            print("❌ No ChromeDriver found in any Railway location")
        except Exception as e:
            print(f"❌ Railway system ChromeDriver failed: {e}")
    
    # Method 2: Selenium 4 Auto-Management (MOST RELIABLE)
    try:
        print("🎯 Method 2: Selenium 4 auto-management...")
        from selenium.webdriver.chrome.service import Service
        
        # Let Selenium 4 handle everything automatically
        service = Service()  # No executable_path specified
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ SUCCESS: Selenium 4 auto-management worked!")
        return driver
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Method 3: WebDriverManager (RELIABLE FALLBACK)
    try:
        print("📦 Method 3: WebDriverManager...")
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        # Force fresh download
        driver_path = ChromeDriverManager(cache_valid_range=1).install()
        print(f"📦 WebDriverManager downloaded ChromeDriver to {driver_path}")
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ SUCCESS: WebDriverManager worked!")
        return driver
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    # Method 4: Direct Chrome without ChromeDriver (EMERGENCY)
    try:
        print("🆘 Method 4: Direct Chrome (emergency)...")
        # Try to use Chrome without specifying ChromeDriver at all
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ SUCCESS: Direct Chrome worked!")
        return driver
    except Exception as e:
        print(f"❌ Method 4 failed: {e}")
    
    # If all methods fail, raise the last exception
    raise Exception("❌ ALL ChromeDriver methods failed. Check Chrome/ChromeDriver installation.")

def format_dict(d):
    vals = list(d.values())
    return "={},".join(d.keys()).format(*vals) + "={}".format(vals[-1])



# Testing: Adding options to undetected chrome driver
def create_stealth_driver():
    """
    Create a stable Chrome driver optimized for Fly.io deployment.
    Removes aggressive flags that cause crashes and uses proven-stable configuration.
    """
    print("🥷 Creating stable Chrome driver for Fly.io...")
    
    # Check if running on Fly.io or Railway
    is_flyio = os.environ.get("FLY_ENVIRONMENT") or os.environ.get("FLY_APP_NAME")
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("CHROME_BIN")
    is_production = is_flyio or is_railway
    
    print(f"🛩️ Fly.io environment detected: {is_flyio}")
    print(f"🚂 Railway environment detected: {is_railway}")
    print(f"🏭 Production environment: {is_production}")
    
    # Production-specific paths
    if is_production:
        chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome-stable")
        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")
        
        print(f"🔍 Checking Chrome binary: {chrome_bin}")
        print(f"   Exists: {os.path.exists(chrome_bin)}")
        print(f"🔍 Checking ChromeDriver: {chromedriver_path}")
        print(f"   Exists: {os.path.exists(chromedriver_path)}")
        
        # If paths don't exist, try alternatives
        if not os.path.exists(chrome_bin):
            alternatives = ["/usr/bin/google-chrome-stable", "/usr/bin/google-chrome", "/usr/bin/chromium-browser"]
            for alt in alternatives:
                if os.path.exists(alt):
                    chrome_bin = alt
                    print(f"✅ Found Chrome alternative: {chrome_bin}")
                    break
        
        if not os.path.exists(chromedriver_path):
            alternatives = ["/usr/local/bin/chromedriver", "/usr/bin/chromedriver", "/app/drivers/chromedriver"]
            for alt in alternatives:
                if os.path.exists(alt):
                    chromedriver_path = alt
                    print(f"✅ Found ChromeDriver alternative: {chromedriver_path}")
                    break
    
    # STABLE Chrome options - optimized for Fly.io 2GB memory
    options = uc.ChromeOptions()
    
    # Core stability flags (REQUIRED for containers)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # Force headless in production
    
    # Memory optimization (optimized for Fly.io 2GB)
    if is_production:
        if is_flyio:
            print("🛩️ Adding Fly.io-optimized Chrome options...")
            # Fly.io specific optimizations for 2GB RAM
            options.add_argument("--max_old_space_size=1024")  # Use more memory on Fly.io
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
        else:
            print("🚂 Adding Railway-optimized Chrome options...")
            # Railway Hobby Plan optimizations
            options.add_argument("--max_old_space_size=512")  # Conservative for Railway
        
        # Common production flags
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--memory-pressure-off")
        
        # Disable unnecessary features (safe removals)
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # For faster loading
        options.add_argument("--disable-notifications")
        options.add_argument("--mute-audio")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        
        # Performance optimizations (proven stable)
        options.add_argument("--disable-features=VizDisplayCompositor,TranslateUI")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")  # For scraping
        options.add_argument("--disable-infobars")
        
        # Set binary location
        options.binary_location = chrome_bin
        print(f"🔧 Chrome binary: {chrome_bin}")
    
    # Download directory preferences
    prefs = {
        "download.default_directory": str(BASE_DIR / "selenium"),
        "profile.managed_default_content_settings.images": 2,  # Block images for speed
        "profile.default_content_setting_values.notifications": 2,  # Block notifications
        "credentials_enable_service": False,  # Disable password manager
        "profile.password_manager_enabled": False,
    }
    
    options.add_experimental_option("prefs", prefs)
    
    # Stealth user agent (realistic)
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    
    # Set window size
    options.add_argument(f"--window-size={BROWSER_WIDTH},{BROWSER_HEIGHT}")
    
    print("🥷 Running stable driver in HEADLESS mode")
    
    # Try to launch undetected Chrome driver with stable config
    try:
        print("🚀 Attempting to create stable undetected Chrome driver...")
        
        # Handle production binary location for UC
        if is_production and chrome_bin:
            print(f"🏗️ Setting Chrome binary location to: {chrome_bin}")
            driver = uc.Chrome(options=options, browser_executable_path=chrome_bin)
        else:
            driver = uc.Chrome(options=options)
        
        # Enhanced session validation with better error handling
        try:
            print("✅ Basic Chrome session validation...")
            driver.get("about:blank")
            
            # Test with a simple, fast page
            print("🧪 Performing lightweight Chrome test...")
            driver.execute_script("return document.readyState")
            
            # Memory check after initialization
            memory_info = get_memory_info()
            if memory_info:
                print(f"📊 Memory after Chrome init: RSS={memory_info.get('memory_rss', 'unknown'):.1f}MB")
            
            if not validate_driver_session(driver):
                raise Exception("Session validation failed")
            
            print("✅ Stable Chrome driver ready for scraping!")
            cache.set('last_chrome_session_time', time.time(), 60)
            return driver
            
        except Exception as test_error:
            print(f"⚠️ Chrome driver created but failed validation: {test_error}")
            try:
                driver.quit()
            except:
                pass
            raise test_error
        
    except Exception as uc_error:
        print(f"⚠️ Undetected Chrome driver failed: {uc_error}")
        print("🔄 Falling back to regular Chrome driver...")
        
        try:
            # Convert UC options to regular ChromeOptions for fallback
            chrome_options = webdriver.ChromeOptions()
            for arg in options.arguments:
                chrome_options.add_argument(arg)
            
            # Add the experimental options
            for key, value in options.experimental_options.items():
                chrome_options.add_experimental_option(key, value)
            
            # Set binary location for regular Chrome
            if is_production and chrome_bin:
                chrome_options.binary_location = chrome_bin
                print(f"🔧 Setting binary location for fallback Chrome: {chrome_bin}")
            
            # Use our improved get_chrome_driver function
            fallback_driver = get_chrome_driver(chrome_options)
            
            # Test the fallback driver session
            try:
                fallback_driver.get("about:blank")
                print("✅ Fallback Chrome driver created and validated successfully")
                return fallback_driver
            except Exception as test_error:
                print(f"⚠️ Fallback Chrome driver failed validation: {test_error}")
                try:
                    fallback_driver.quit()
                except:
                    pass
                raise test_error
            
        except Exception as fallback_error:
            print(f"❌ Both Chrome drivers failed: {fallback_error}")
            raise fallback_error

def get_memory_info():
    """
    Get current memory usage information for debugging.
    Returns a dictionary with memory stats or None if unavailable.
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Create memory stats dictionary
        memory_stats = {
            'memory_rss': memory_info.rss / 1024 / 1024,  # MB
            'memory_vms': memory_info.vms / 1024 / 1024,  # MB
        }
        
        print(f"📊 Memory usage: RSS={memory_stats['memory_rss']:.1f}MB, VMS={memory_stats['memory_vms']:.1f}MB")
        
        # System memory info
        try:
            sys_memory = psutil.virtual_memory()
            memory_stats.update({
                'system_percent': sys_memory.percent,
                'system_available': sys_memory.available / 1024 / 1024,  # MB
            })
            print(f"📊 System memory: {memory_stats['system_percent']}% used, {memory_stats['system_available']:.1f}MB available")
        except Exception as sys_error:
            print(f"⚠️ Could not get system memory info: {sys_error}")
        
        return memory_stats
        
    except Exception as e:
        print(f"⚠️ Could not get memory info: {e}")
        return None

def safe_create_stealth_driver():
    """
    Create Chrome driver with global session management and retry logic to prevent conflicts.
    """
    # Use a global lock to prevent multiple Chrome sessions from being created simultaneously
    with chrome_session_lock:
        # Add delay to prevent rapid session creation/destruction
        time.sleep(2)
        
        # Check if a session was recently created
        last_session_time = cache.get('last_chrome_session_time', 0)
        current_time = time.time()
        
        # Ensure at least 5 seconds between Chrome sessions
        if current_time - last_session_time < 5:
            wait_time = 5 - (current_time - last_session_time)
            print(f"🕐 Waiting {wait_time:.1f}s before creating new Chrome session...")
            time.sleep(wait_time)
        
        # Monitor memory before creating driver
        print("📊 Memory info before Chrome creation:")
        get_memory_info()
        
        # Retry logic for session creation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🚀 Creating new Chrome session (attempt {attempt + 1}/{max_retries})...")
                driver = create_stealth_driver()
                
                # Monitor memory after creating driver
                print("📊 Memory info after Chrome creation:")
                get_memory_info()
                
                # Validate session is working
                try:
                    driver.get("about:blank")
                    print("✅ Basic Chrome session validation passed")
                    
                    # ENHANCED: Stress test with a moderately complex page
                    print("🧪 Performing Chrome stress test...")
                    driver.get("https://example.com")
                    time.sleep(2)
                    
                    if not validate_driver_session(driver):
                        raise Exception("Session failed during stress test")
                    
                    print("✅ Chrome stress test passed - ready for Morningstar!")
                    cache.set('last_chrome_session_time', time.time(), 60)
                    return driver
                except Exception as test_error:
                    print(f"⚠️ Undetected Chrome driver created but failed session test: {test_error}")
                    try:
                        driver.quit()
                    except:
                        pass
                    raise test_error
                
            except Exception as e:
                print(f"❌ Chrome session creation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    print(f"❌ All {max_retries} session creation attempts failed")
                    raise e

def safe_close_driver(driver):
    """
    Safely close Chrome driver with proper cleanup.
    """
    if driver:
        try:
            # First, check if the driver is still responsive
            try:
                driver.current_url  # Test if session is alive
            except Exception as e:
                print(f"⚠️ Driver session already dead: {e}")
                return  # Session already closed
            
            # Close all windows first
            try:
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    driver.close()
            except Exception as e:
                print(f"⚠️ Error closing windows: {e}")
        except Exception as e:
            print(f"⚠️ Error during initial cleanup: {e}")
        
        try:
            # Quit the driver
            driver.quit()
            print("🔄 Chrome session closed successfully")
        except Exception as e:
            print(f"⚠️ Warning: Error closing Chrome session: {e}")
        
        # Add delay after closing to prevent rapid reopening
        time.sleep(1)

def validate_driver_session(driver):
    """
    Validate that a Chrome driver session is still alive and responsive.
    Returns True if valid, False if session is dead.
    """
    try:
        # Test basic session functionality
        driver.current_url
        driver.title
        return True
    except Exception as e:
        print(f"⚠️ Driver session validation failed: {e}")
        return False

@shared_task(bind=True)
def scraper(self,ticker_value,market_value,download_type):
    """
    RAILWAY HOBBY PLAN OPTIMIZED: Ultra-lightweight scraper with aggressive resource management.
    """
    print(f"🎯 HOBBY PLAN: Starting minimal scraper for {download_type} - {ticker_value} ({market_value})")
    
    # HOBBY PLAN: Try lightweight fallback FIRST
    print("🔄 HOBBY PLAN: Attempting lightweight scraper first...")
    fallback_data = scrape_with_requests_fallback(ticker_value, market_value, download_type)
    
    if fallback_data:
        print("✅ HOBBY PLAN: Lightweight scraping succeeded!")
        if download_type == "INCOME_STATEMENT":
            database.child("income_statement").set({"income_statement": fallback_data})
        elif download_type == "BALANCE_SHEET":
            database.child("balance_sheet").set({"balance_sheet": fallback_data})
        elif download_type == "CASH_FLOW":
            database.child("cash_flow").set({"cash_flow": fallback_data})
        return 'DONE'
    
    print("⚠️ HOBBY PLAN: Lightweight scraping failed, trying minimal Chrome...")
    
    max_retries = 1  # HOBBY PLAN: Reduce retries to save resources
    
    for task_attempt in range(max_retries):
        driver = None
        try:
            print(f"📝 HOBBY PLAN: Task attempt {task_attempt + 1}/{max_retries}")
            
            # HOBBY PLAN: Create ultra-minimal Chrome driver
            driver = create_hobby_plan_driver()
            
            if not validate_driver_session(driver):
                raise Exception("Initial session validation failed")
            
            # HOBBY PLAN: Direct navigation without retries
            navigation_url = f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials"
            print(f"🌐 HOBBY PLAN: Direct navigation to {navigation_url}")
            
            driver.set_page_load_timeout(30)  # Shorter timeout
            driver.get(navigation_url)
            
            # Quick validation
            if not validate_driver_session(driver):
                raise Exception("Session failed after navigation")
            
            print("✅ HOBBY PLAN: Navigation successful!")
            
            if download_type == "BALANCE_SHEET":
                print(f"📊 HOBBY PLAN: Quick balance sheet scraping...")
                
                # ULTRA-MINIMAL: Skip detailed view, just export what's available
                try:
                    # Click Balance Sheet if not already selected
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.common.by import By
                    
                    # Quick click without detailed waiting
                    try:
                        balance_sheet_btn = driver.find_element(By.XPATH, "//button[contains(., 'Balance Sheet')]")
                        balance_sheet_btn.click()
                        time.sleep(2)
                    except:
                        print("⚠️ HOBBY PLAN: Balance sheet already selected or not found")
                    
                    # Try immediate export
                    try:
                        export_btn = driver.find_element(By.XPATH, "//button[contains(., 'Export') or @aria-label='Export']")
                        export_btn.click()
                        time.sleep(5)  # Shorter wait
                        print("✅ HOBBY PLAN: Export triggered")
                    except:
                        print("⚠️ HOBBY PLAN: Export button not found, trying table scraping")
                        
                        # Fallback: Try to get table data directly
                        try:
                            import pandas as pd
                            tables = driver.find_elements(By.TAG_NAME, "table")
                            if tables:
                                table_html = tables[0].get_attribute("outerHTML")
                                df = pd.read_html(table_html)[0]
                                data1 = df.to_json()
                                database.child("balance_sheet").set({"balance_sheet": data1})
                                print("✅ HOBBY PLAN: Table data scraped successfully")
                                safe_close_driver(driver)
                                return 'DONE'
                        except Exception as table_error:
                            print(f"⚠️ HOBBY PLAN: Table scraping failed: {table_error}")
                    
                    # Try to read downloaded file
                    try:
                        import pandas as pd
                        excel_file = BASE_DIR / "selenium" / "Balance Sheet_Annual_As Originally Reported.xls"
                        if excel_file.exists():
                            excel_data_df = pd.read_excel(excel_file)
                            data1 = excel_data_df.to_json()
                            database.child("balance_sheet").set({"balance_sheet": data1})
                            print("✅ HOBBY PLAN: Excel file processed")
                        else:
                            print("⚠️ HOBBY PLAN: Excel file not found")
                            raise Exception("No data file found")
                    except Exception as excel_error:
                        print(f"⚠️ HOBBY PLAN: Excel processing failed: {excel_error}")
                        raise excel_error
                        
                except Exception as scraping_error:
                    print(f"❌ HOBBY PLAN: Balance sheet scraping failed: {scraping_error}")
                    x = '{"balance_sheet":{"none":"no data"}}'
                    database.child("balance_sheet").set({"balance_sheet": x})
                
            # HOBBY PLAN: Immediate cleanup and return
            safe_close_driver(driver)
            return 'DONE'
                
        except Exception as session_error:
            print(f"❌ HOBBY PLAN: Session error: {session_error}")
            safe_close_driver(driver)
            
            # HOBBY PLAN: No retries, immediate fallback
            print("❌ HOBBY PLAN: Setting fallback data immediately")
            if download_type == "INCOME_STATEMENT":
                x = '{"income_statement":{"none":"no data"}}'
                database.child("income_statement").set({"income_statement": x})
            elif download_type == "BALANCE_SHEET":
                x = '{"balance_sheet":{"none":"no data"}}'
                database.child("balance_sheet").set({"balance_sheet": x})
            elif download_type == "CASH_FLOW":
                x = '{"cash_flow":{"none":"no data"}}'
                database.child("cash_flow").set({"cash_flow": x})
            return 'ERROR'
        
        finally:
            safe_close_driver(driver)
    
    return 'ERROR'

def create_hobby_plan_driver():
    """
    Create ultra-minimal Chrome driver specifically optimized for Railway Hobby Plan (512MB-1GB).
    Uses absolute minimum flags to prevent resource exhaustion.
    """
    print("🔧 HOBBY PLAN: Creating ultra-minimal Chrome driver...")
    
    # HOBBY PLAN: Use regular Chrome (not undetected) to save memory
    options = webdriver.ChromeOptions()
    
    # HOBBY PLAN: Only essential flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    
    # HOBBY PLAN: Ultra-aggressive memory management
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=256")  # Ultra-low
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Critical for memory saving
    options.add_argument("--disable-css")  # Disable CSS processing
    options.add_argument("--disable-javascript")  # Disable JS to save memory
    options.add_argument("--no-first-run")
    options.add_argument("--disable-default-apps")
    
    # HOBBY PLAN: Minimal window
    options.add_argument("--window-size=800,600")  # Smaller window
    
    # Set Chrome binary
    chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome-stable")
    if os.path.exists(chrome_bin):
        options.binary_location = chrome_bin
        print(f"🔧 HOBBY PLAN: Chrome binary: {chrome_bin}")
    
    try:
        # HOBBY PLAN: Use regular Chrome WebDriver (lighter than UC)
        from selenium.webdriver.chrome.service import Service
        
        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")
        if os.path.exists(chromedriver_path):
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ HOBBY PLAN: Ultra-minimal Chrome driver created")
            return driver
        else:
            # Fallback to auto-detection
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ HOBBY PLAN: Auto-detected Chrome driver created")
            return driver
            
    except Exception as e:
        print(f"❌ HOBBY PLAN: Ultra-minimal driver failed: {e}")
        raise e

@shared_task(bind=True)
def scraper_dividends(self, ticker_value, market_value):
    """
    Scraper task for dividends data with improved error handling.
    """
    print(f"🎯 Starting dividends scraper for {ticker_value} ({market_value})")
    
    driver_dividends = None
    try:
        # Create Chrome driver with fallback mechanism (same as scraper function)
        driver_dividends = safe_create_stealth_driver()
        
        print(f"Starting dividends scraping for {ticker_value}")
        driver_dividends.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/dividends")
        print(f"Current URL: {driver_dividends.current_url}")
        
        # Debug: Check what elements are available on the page
        try:
            tables = driver_dividends.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables on page")
            
            divs = driver_dividends.find_elements(By.TAG_NAME, "div")
            table_divs = [div for div in divs if 'table' in div.get_attribute('class').lower()]
            print(f"Found {len(table_divs)} table-related divs on page")
        except Exception as e:
            print(f"Error getting page elements: {e}")
        
        # Try multiple strategies to find the dividends table
        data_found = False
        data = None
        
        try:
            # Strategy 1: Original selector
            data = WebDriverWait(driver_dividends, 30).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))
            ).get_attribute("outerHTML")
            data_found = True
            print("Successfully found dividends table (Strategy 1)")
        except:
            try:
                # Strategy 2: Look for any table scroller
                data = WebDriverWait(driver_dividends, 30).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'table__scroller')]"))
                ).get_attribute("outerHTML")
                data_found = True
                print("Successfully found dividends table (Strategy 2)")
            except:
                try:
                    # Strategy 3: Look for any table container
                    data = WebDriverWait(driver_dividends, 30).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'table') and contains(@class, 'scroller')]"))
                    ).get_attribute("outerHTML")
                    data_found = True
                    print("Successfully found dividends table (Strategy 3)")
                except:
                    try:
                        # Strategy 4: Look for direct table element
                        table_element = WebDriverWait(driver_dividends, 30).until(
                            EC.visibility_of_element_located((By.TAG_NAME, "table"))
                        )
                        data = table_element.get_attribute("outerHTML")
                        data_found = True
                        print("Successfully found dividends table (Strategy 4)")
                    except:
                        print("Warning: Could not find dividends table with any strategy")
        
        if data_found and data:
            try:
                df = pd.read_html(data)
                if df and len(df) > 0:
                    data1 = df[0].to_json()
                    print("Successfully parsed dividends data")
                    print(f"Data preview: {data1[:200]}...")  # Show first 200 chars
                    database.child("dividends").set({"dividends": data1})
                else:
                    print("Warning: No data found in parsed HTML")
                    x = '{"dividends":{"none":"no data"}}'
                    database.child("dividends").set({"dividends": x})
            except Exception as e:
                print(f"Error parsing dividends data: {e}")
                x = '{"dividends":{"none":"no data"}}'
                database.child("dividends").set({"dividends": x})
        else:
            print("No dividends data found")
            x = '{"dividends":{"none":"no data"}}'
            database.child("dividends").set({"dividends": x})
            
        sleep(10)
        return 'DONE'
        
    except Exception as e:
        print(f"❌ Error in scraper_dividends: {e}")
        x = '{"dividends":{"none":"no data"}}'
        database.child("dividends").set({"dividends": x})
        return 'ERROR'
    finally:
        safe_close_driver(driver_dividends)

@shared_task()
def scraper_valuation(ticker_value,market_value,download_type):
    """
    Scraper task for valuation data with improved error handling.
    """
    print(f"🎯 Starting valuation scraper: {download_type} for {ticker_value} ({market_value})")
    
    valuation_driver = None
    try:
        # Create Chrome driver with fallback mechanism (same as scraper_dividends)
        valuation_driver = safe_create_stealth_driver()
        
        print(f"Starting valuation scraping for {ticker_value}, type: {download_type}")
        valuation_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/key-metrics")
        print(f"Current URL: {valuation_driver.current_url}")
        
        # Wait for page to load
        sleep(3)
        
        # Click the appropriate tab based on download_type FIRST
        tab_clicked = False
        if download_type == "VALUATION_CASH_FLOW":
            # Click Cash Flow tab
            try:
                # Strategy 1: By ID
                WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.ID, "keyMetricscashFlow"))).click()
                tab_clicked = True
                print("Successfully clicked Cash Flow tab (Strategy 1)")
            except:
                try:
                    # Strategy 2: By data attribute
                    WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@data='cashFlow']"))).click()
                    tab_clicked = True
                    print("Successfully clicked Cash Flow tab (Strategy 2)")
                except:
                    try:
                        # Strategy 3: By text content
                        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
                        tab_clicked = True
                        print("Successfully clicked Cash Flow tab (Strategy 3)")
                    except:
                        print("Warning: Could not find Cash Flow tab")
                        
        elif download_type == "VALUATION_GROWTH":
            # Click Growth tab
            try:
                # Strategy 1: By ID
                WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.ID, "keyMetricsgrowthTable"))).click()
                tab_clicked = True
                print("Successfully clicked Growth tab (Strategy 1)")
            except:
                try:
                    # Strategy 2: By data attribute
                    WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@data='growthTable']"))).click()
                    tab_clicked = True
                    print("Successfully clicked Growth tab (Strategy 2)")
                except:
                    try:
                        # Strategy 3: By text content (exact match for Growth to avoid confusion)
                        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Growth' or contains(., 'Growth') and not(contains(., 'Growth Rate'))]"))).click()
                        tab_clicked = True
                        print("Successfully clicked Growth tab (Strategy 3)")
                    except:
                        print("Warning: Could not find Growth tab")
                        
        elif download_type == "VALUATION_FINANCIAL_HEALTH":
            # Click Financial Health tab
            try:
                # Strategy 1: By ID
                WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.ID, "keyMetricsfinancialHealth"))).click()
                tab_clicked = True
                print("Successfully clicked Financial Health tab (Strategy 1)")
            except:
                try:
                    # Strategy 2: By data attribute
                    WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@data='financialHealth']"))).click()
                    tab_clicked = True
                    print("Successfully clicked Financial Health tab (Strategy 2)")
                except:
                    try:
                        # Strategy 3: By text content
                        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Financial Health')]"))).click()
                        tab_clicked = True
                        print("Successfully clicked Financial Health tab (Strategy 3)")
                    except:
                        print("Warning: Could not find Financial Health tab")
                        
        elif download_type == "VALUATION_OPERATING_EFFICIENCY":
            # Click Profitability and Efficiency tab
            try:
                # Strategy 1: By ID
                WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.ID, "keyMetricsprofitabilityAndEfficiency"))).click()
                tab_clicked = True
                print("Successfully clicked Profitability and Efficiency tab (Strategy 1)")
            except:
                try:
                    # Strategy 2: By data attribute
                    WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@data='profitabilityAndEfficiency']"))).click()
                    tab_clicked = True
                    print("Successfully clicked Profitability and Efficiency tab (Strategy 2)")
                except:
                    try:
                        # Strategy 3: By text content
                        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Profitability and Efficiency')]"))).click()
                        tab_clicked = True
                        print("Successfully clicked Profitability and Efficiency tab (Strategy 3)")
                    except:
                        try:
                            # Strategy 4: Shorter text match
                            WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Profitability')]"))).click()
                            tab_clicked = True
                            print("Successfully clicked Profitability tab (Strategy 4)")
                        except:
                            print("Warning: Could not find Profitability and Efficiency tab")
        
        if tab_clicked:
            sleep(3)  # Wait for tab content to load
            print(f"Successfully navigated to {download_type} tab")
        else:
            print(f"Using default tab for {download_type}")
        
        # NOW select "10 Years" time period after tab is selected
        # Try multiple strategies to find and click the time period dropdown (currently showing "5 Years")
        time_period_clicked = False
        try:
            # Strategy 1: Find button containing "5 Years" text
            WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '5 Years')]"))).click()
            time_period_clicked = True
            print("Successfully clicked 5 Years dropdown (Strategy 1)")
        except:
            try:
                # Strategy 2: Find button with specific classes
                WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'mds-button--secondary') and contains(., 'Years')]"))).click()
                time_period_clicked = True
                print("Successfully clicked time period dropdown (Strategy 2)")
            except:
                try:
                    # Strategy 3: Find any button with "Years" text and aria-haspopup
                    WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-haspopup='true' and contains(., 'Years')]"))).click()
                    time_period_clicked = True
                    print("Successfully clicked time period dropdown (Strategy 3)")
                except:
                    print("Warning: Could not find time period dropdown button")
        
        if time_period_clicked:
            sleep(2)  # Wait for dropdown to open
            
            # Try multiple strategies to find and click "10 Years" option
            ten_years_selected = False
            try:
                # Strategy 1: Direct text match
                WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '10 Years')] | //li[contains(., '10 Years')] | //div[contains(., '10 Years')]"))).click()
                ten_years_selected = True
                print("Successfully selected 10 Years option (Strategy 1)")
            except:
                try:
                    # Strategy 2: Look for clickable element with "10" and "Years"
                    WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(., '10') and contains(., 'Years')]"))).click()
                    ten_years_selected = True
                    print("Successfully selected 10 Years option (Strategy 2)")
                except:
                    try:
                        # Strategy 3: Look in dropdown menu or list items
                        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//ul//li[contains(text(), '10')] | //div[@role='menu']//div[contains(text(), '10')]"))).click()
                        ten_years_selected = True
                        print("Successfully selected 10 Years option (Strategy 3)")
                    except:
                        print("Warning: Could not find 10 Years option in dropdown")
            
            if ten_years_selected:
                sleep(3)  # Wait for page to reload with 10-year data
                print("Successfully set time period to 10 years")
            else:
                print("Using default time period (could not select 10 years)")
        else:
            print("Using default time period (could not open dropdown)")
        
        # Click the export button to download XLS file
        export_clicked = False
        try:
            # Strategy 1: By ID (salKeyStatsPopoverExport)
            WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.ID, "salKeyStatsPopoverExport"))).click()
            export_clicked = True
            print("Successfully clicked Export button by ID (Strategy 1)")
        except:
            try:
                # Strategy 2: By aria-label
                WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Export']"))).click()
                export_clicked = True
                print("Successfully clicked Export button by aria-label (Strategy 2)")
            except:
                try:
                    # Strategy 3: By class and icon combination
                    WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'mds-button--icon-only__sal') and .//span[@data-mds-icon-name='share']]"))).click()
                    export_clicked = True
                    print("Successfully clicked Export button by class/icon (Strategy 3)")
                except:
                    try:
                        # Strategy 4: Look in export div
                        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='export']//button"))).click()
                        export_clicked = True
                        print("Successfully clicked Export button in export div (Strategy 4)")
                    except:
                        print("Warning: Could not find Export button")
        
        if export_clicked:
            sleep(10)  # Wait for download to complete
            print("Waiting for download to complete...")
            
            # Read the downloaded file based on download_type
            try:
                if download_type == "VALUATION_CASH_FLOW":
                    excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "cashFlow.xls")
                    data1 = excel_data_df.to_json()
                    print("Successfully read cash flow valuation Excel file")
                    print(data1)
                    database.child("valuation_cash_flow").set({"valuation_cash_flow": data1})
                elif download_type == "VALUATION_GROWTH":
                    excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "growthTable.xls")
                    data1 = excel_data_df.to_json()
                    print("Successfully read growth valuation Excel file")
                    print(data1)
                    database.child("valuation_growth").set({"valuation_growth": data1})
                elif download_type == "VALUATION_FINANCIAL_HEALTH":
                    excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "financialHealth.xls")
                    data1 = excel_data_df.to_json()
                    print("Successfully read financial health valuation Excel file")
                    print(data1)
                    database.child("valuation_financial_health").set({"valuation_financial_health": data1})
                elif download_type == "VALUATION_OPERATING_EFFICIENCY":
                    excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "operatingAndEfficiency.xls")
                    data1 = excel_data_df.to_json()
                    print("Successfully read operating efficiency valuation Excel file")
                    print(data1)
                    database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": data1})
            except Exception as e:
                print(f"Error reading Excel file for {download_type}: {e}")
                # Set fallback data based on download_type
                if download_type == "VALUATION_CASH_FLOW":
                    x = '{"valuation_cash_flow":{"none":"no data"}}'
                    database.child("valuation_cash_flow").set({"valuation_cash_flow": x})
                elif download_type == "VALUATION_GROWTH":
                    x = '{"valuation_growth":{"none":"no data"}}'
                    database.child("valuation_growth").set({"valuation_growth": x})
                elif download_type == "VALUATION_FINANCIAL_HEALTH":
                    x = '{"valuation_financial_health":{"none":"no data"}}'
                    database.child("valuation_financial_health").set({"valuation_financial_health": x})
                elif download_type == "VALUATION_OPERATING_EFFICIENCY":
                    x = '{"valuation_operating_efficiency":{"none":"no data"}}'
                    database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": x})
        else:
            print("Export failed, setting fallback data")
            # Set fallback data based on download_type
            if download_type == "VALUATION_CASH_FLOW":
                x = '{"valuation_cash_flow":{"none":"no data"}}'
                database.child("valuation_cash_flow").set({"valuation_cash_flow": x})
            elif download_type == "VALUATION_GROWTH":
                x = '{"valuation_growth":{"none":"no data"}}'
                database.child("valuation_growth").set({"valuation_growth": x})
            elif download_type == "VALUATION_FINANCIAL_HEALTH":
                x = '{"valuation_financial_health":{"none":"no data"}}'
                database.child("valuation_financial_health").set({"valuation_financial_health": x})
            elif download_type == "VALUATION_OPERATING_EFFICIENCY":
                x = '{"valuation_operating_efficiency":{"none":"no data"}}'
                database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": x})
                
        sleep(5)
        return 'DONE'
    except Exception as e:
        print(f"❌ Error in scraper_valuation: {e}")
        # Set appropriate error data based on download_type
        if download_type == "VALUATION_CASH_FLOW":
            x = '{"valuation_cash_flow":{"none":"no data"}}'
            database.child("valuation_cash_flow").set({"valuation_cash_flow": x})
        elif download_type == "VALUATION_GROWTH":
            x = '{"valuation_growth":{"none":"no data"}}'
            database.child("valuation_growth").set({"valuation_growth": x})
        elif download_type == "VALUATION_FINANCIAL_HEALTH":
            x = '{"valuation_financial_health":{"none":"no data"}}'
            database.child("valuation_financial_health").set({"valuation_financial_health": x})
        elif download_type == "VALUATION_OPERATING_EFFICIENCY":
            x = '{"valuation_operating_efficiency":{"none":"no data"}}'
            database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": x})
        return 'ERROR'
    finally:
        safe_close_driver(valuation_driver)

@shared_task(bind=True)
def all_scraper(self,ticker_value,market_value):
    CHROME_DRIVER_PATH = BASE_DIR / "chromedriver"
    prefs = {'download.default_directory' :  str(BASE_DIR / "selenium")}
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option('prefs', prefs)
    chromeOptions.add_argument("--disable-infobars")
    chromeOptions.add_argument("--start-maximized")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--window-size=1920,1080")
    chromeOptions.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chromeOptions.add_argument('--no-sandbox')   
    chromeOptions.add_argument("--disable-dev-shm-usage")
    
    # Create Chrome driver with automatic environment detection
    valuation_financial_health_driver = get_chrome_driver(chromeOptions)
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
    
    # Debug: Save page source and screenshot for troubleshooting
    try:
        print(f"Page title: {valuation_financial_health_driver.title}")
        print(f"Current URL: {valuation_financial_health_driver.current_url}")
        
        # Save page source for debugging
        with open(f"debug_page_source_{ticker_value}.html", "w", encoding="utf-8") as f:
            f.write(valuation_financial_health_driver.page_source)
        
        # Take screenshot for debugging
        valuation_financial_health_driver.save_screenshot(f"debug_screenshot_{ticker_value}.png")
        
        WebDriverWait(valuation_financial_health_driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Financial Health')]"))).click()
    except Exception as e:
        print(f"Error finding Financial Health button: {e}")
        print("Available buttons on page:")
        buttons = valuation_financial_health_driver.find_elements(By.TAG_NAME, "button")
        for i, button in enumerate(buttons[:10]):  # Show first 10 buttons
            print(f"Button {i}: '{button.text}' - visible: {button.is_displayed()}")
        raise e
    try:
        WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "financialHealth.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("valuation_financial_health").set({"valuation_financial_health": data1 })
    except:
         x =  '{"valuation_financial_health":{"none":"no data"}}'
         database.child("valuation_financial_health").set({"valuation_financial_health": x })
    sleep(10)
    WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Operating and Efficiency')]"))).click()
    try:
        WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "operatingAndEfficiency.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": data1 })
    except:
        x =  '{"valuation_operating_efficiency":{"none":"no data"}}'
        database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": x })
    sleep(10)
    WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
    try:
        WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "cashFlow.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("valuation_cash_flow").set({"valuation_cash_flow": data1 })
    except:
        x =  '{"valuation_cash_flow":{"none":"no data"}}'
        database.child("valuation_cash_flow").set({"valuation_cash_flow": x })
    sleep(10)    
    WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Growth')]"))).click()
    try:
        WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "growthTable.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("valuation_growth").set({"valuation_growth": data1 })
    except:
        x =  '{"valuation_growth":{"none":"no data"}}'
        database.child("valuation_growth").set({"valuation_growth": x })

    sleep(10)
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/performance")
    try:
        data = WebDriverWait(valuation_financial_health_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        data1 = df[0].to_json()
        print(data1)
        database.child("operating_performance").set({"operating_performance": data1 })
    except:
         x =  '{"operating_performance":{"none":"no data"}}'
         database.child("operating_performance").set({"operating_performance": x })

    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/dividends")
    try:
        data = WebDriverWait(valuation_financial_health_driver, 50).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)   
        data1 = df[0].to_json()
        print(data1)
        database.child("dividends").set({"dividends": data1 })
    except:
        x =  '{"dividends":{"none":"no data"}}'
        database.child("dividends").set({"dividends": x })
    sleep(10)
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
    sleep(10)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Income Statement')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
    sleep(10)
    try:
        excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "Income Statement_Annual_As Originally Reported.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("income_statement").set({"income_statement": data1 })
    except Exception as e:
        print(f"Error reading income statement Excel file: {e}")
        x =  '{"income_statement":{"none":"no data"}}'
        database.child("income_statement").set({"income_statement": x })
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Balance Sheet')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
    sleep(10)
    try:
            excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "Balance Sheet_Annual_As Originally Reported.xls")
            data1 = excel_data_df.to_json()
            print(data1)
            database.child("balance_sheet").set({"balance_sheet": data1 })
    except Exception as e:
        print(f"Error reading balance sheet Excel file: {e}")
        x =  '{"balance_sheet":{"none":"no data"}}'
        database.child("balance_sheet").set({"balance_sheet": x })
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
    sleep(10)
    try:
        excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "Cash Flow_Annual_As Originally Reported.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("cash_flow").set({"cash_flow": data1 })
    except:
        x =  '{"cash_flow":{"none":"no data"}}'
        database.child("cash_flow").set({"cash_flow": x })
    sleep(10)
    valuation_financial_health_driver.quit() 
    return 'DONE'    



@shared_task()
def scraper_operating_performance(ticker_value, market_value):
    CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
    prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option('prefs', prefs)
    chromeOptions.add_argument("--disable-infobars")
    chromeOptions.add_argument("--start-maximized")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--window-size=1920,1080")
    chromeOptions.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chromeOptions.add_argument('--no-sandbox')   
    chromeOptions.add_argument("--disable-dev-shm-usage")
    
    # Create Chrome driver with automatic environment detection
    driver_operating_perfomance = get_chrome_driver(chromeOptions)
    driver_operating_perfomance.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/performance")
    try:
        data = WebDriverWait(driver_operating_perfomance, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        data1 = df[0].to_json()
        print(data1)
        database.child("operating_performance").set({"operating_performance": data1 })
    except:
        x =  '{"operating_performance":{"none":"no data"}}'
        database.child("operating_performance").set({"operating_performance": x })
    sleep(10)
    driver_operating_perfomance.quit()
    return 'DONE'

def safe_navigate_with_retry(driver, url, max_retries=3):
    """
    Navigate to a URL with retry logic and resource management.
    Enhanced with Chrome crash detection and recovery.
    """
    for attempt in range(max_retries):
        try:
            print(f"🌐 Navigation attempt {attempt + 1}/{max_retries} to: {url}")
            
            # Validate session is alive before starting
            if not validate_driver_session(driver):
                raise Exception("Session is already dead before navigation")
            
            # Set page load timeout to prevent hanging
            driver.set_page_load_timeout(45)  # Reduced from 60 to 45 seconds
            
            # Test simple navigation first if this is the first attempt
            if attempt == 0:
                print("🧪 Testing basic navigation capability...")
                driver.get("about:blank")
                time.sleep(1)
                
                if not validate_driver_session(driver):
                    raise Exception("Session failed after basic navigation test")
                print("✅ Basic navigation test passed")
                
                # Test a simple external website to verify internet connectivity
                print("🌐 Testing external connectivity...")
                try:
                    driver.get("https://httpbin.org/get")
                    time.sleep(2)
                    
                    if not validate_driver_session(driver):
                        raise Exception("Session failed after connectivity test")
                    print("✅ External connectivity test passed")
                except Exception as e:
                    print(f"⚠️ Connectivity test failed: {e}")
                    # Don't fail completely, just log and continue
            
            # ENHANCED: Pre-navigate memory cleanup
            print("🧹 Pre-navigation cleanup...")
            try:
                # Clear any existing cookies/cache
                driver.delete_all_cookies()
                print("   ✅ Cookies cleared")
            except Exception as e:
                print(f"   ⚠️ Cookie clear failed: {e}")
            
            # Monitor memory before navigation
            print("📊 Memory before navigation:")
            get_memory_info()
            
            # Navigate to target URL with additional error handling
            print(f"🎯 Navigating to target URL...")
            try:
                driver.get(url)
                print(f"🔗 Navigation request sent to: {url}")
            except Exception as nav_exception:
                print(f"❌ Navigation request failed: {nav_exception}")
                
                # Check if it's a session crash
                if "invalid session id" in str(nav_exception).lower() or "session deleted" in str(nav_exception).lower():
                    print("💥 Chrome session crashed during navigation!")
                    raise Exception(f"Chrome crash detected: {nav_exception}")
                else:
                    raise nav_exception
            
            # Validate navigation completed
            print("🔍 Validating navigation result...")
            if not validate_driver_session(driver):
                raise Exception("Session failed after navigation")
            
            # Check if we actually reached the target URL
            current_url = driver.current_url
            print(f"📍 Current URL: {current_url}")
            
            # Wait for page to stabilize with periodic session checks
            for i in range(3):  # 3 checks over 6 seconds
                time.sleep(2)
                if not validate_driver_session(driver):
                    raise Exception(f"Session failed during page stabilization (check {i+1})")
                print(f"   ✅ Session stable check {i+1}/3")
            
            # Monitor memory after navigation
            print("📊 Memory after navigation:")
            get_memory_info()
            
            print(f"✅ Successfully navigated to: {current_url}")
            return True
            
        except Exception as nav_error:
            print(f"❌ Navigation attempt {attempt + 1} failed: {nav_error}")
            
            # Enhanced error analysis
            error_str = str(nav_error).lower()
            is_session_crash = any(keyword in error_str for keyword in [
                "invalid session id", "session deleted", "chrome crash", 
                "browser has closed", "disconnected", "renderer"
            ])
            
            if is_session_crash:
                print("💥 Chrome session crash detected!")
                print("   This indicates Chrome ran out of memory or crashed")
                print("   Session is no longer usable - caller should recreate driver")
                raise Exception(f"Chrome session crashed and must be recreated: {nav_error}")
            
            # For non-crash errors, check if session is still alive
            if not validate_driver_session(driver):
                print("💀 Session died but not from a recognized crash pattern")
                raise Exception(f"Chrome session died during navigation: {nav_error}")
            
            if attempt < max_retries - 1:
                print(f"🔄 Retrying navigation in 5 seconds...")
                time.sleep(5)
            else:
                raise Exception(f"All {max_retries} navigation attempts failed: {nav_error}")
    
    return False

def scrape_with_requests_fallback(ticker_value, market_value, download_type):
    """
    Lightweight fallback scraping method using requests instead of Chrome.
    Used when Chrome crashes on heavy websites like Morningstar.
    Optimized for Railway Hobby Plan constraints.
    """
    print("🔄 Attempting lightweight scraping fallback for Hobby Plan...")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Use a simple requests session with minimal headers for hobby plan
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
        # Try simpler, lighter endpoints first for hobby plan
        urls_to_try = [
            # Try Yahoo Finance first (lighter than Morningstar)
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker_value}?modules=financialData",
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker_value}?modules=incomeStatementHistory",
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker_value}?modules=balanceSheetHistory", 
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker_value}?modules=cashflowStatementHistory",
            # Yahoo Finance web scraping (lighter)
            f"https://finance.yahoo.com/quote/{ticker_value}/financials",
            f"https://finance.yahoo.com/quote/{ticker_value}/balance-sheet",
            f"https://finance.yahoo.com/quote/{ticker_value}/cash-flow",
            # Last resort: Morningstar simple pages
            f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}",
        ]
        
        for url in urls_to_try:
            try:
                print(f"🔍 Trying fallback URL: {url}")
                response = session.get(url, timeout=15)  # Shorter timeout for hobby plan
                
                if response.status_code == 200:
                    # Try to parse JSON data if available
                    if 'application/json' in response.headers.get('content-type', ''):
                        data = response.json()
                        print(f"✅ Got JSON data from {url}")
                        
                        # Extract relevant financial data from Yahoo Finance API response
                        if 'quoteSummary' in data and data['quoteSummary']['result']:
                            result = data['quoteSummary']['result'][0]
                            
                            # Convert to simplified format
                            simplified_data = {}
                            for module_name, module_data in result.items():
                                if isinstance(module_data, dict):
                                    simplified_data[module_name] = module_data
                            
                            return json.dumps(simplified_data)
                        else:
                            return json.dumps(data)
                    
                    # Try to parse HTML and extract tables (for web pages)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    tables = soup.find_all('table')
                    
                    if tables:
                        print(f"✅ Found {len(tables)} tables in HTML from {url}")
                        try:
                            # Convert first table to JSON
                            import pandas as pd
                            df = pd.read_html(str(tables[0]))[0]
                            return df.to_json()
                        except Exception as table_error:
                            print(f"⚠️ Could not parse table: {table_error}")
                            # Return basic data structure
                            return json.dumps({"source": url, "data": "table_found_but_unparseable"})
                        
            except Exception as e:
                print(f"⚠️ Fallback URL {url} failed: {e}")
                continue
        
        print("❌ All fallback URLs failed")
        return None
        
    except Exception as e:
        print(f"❌ Requests fallback failed: {e}")
        return None

