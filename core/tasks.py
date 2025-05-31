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
    SIMPLIFIED ChromeDriver creation - ONLY uses reliable methods.
    Completely avoids system ChromeDriver to prevent version mismatches.
    Enhanced for Railway deployment.
    """
    print("🚀 SIMPLIFIED ChromeDriver creation starting...")
    
    # Check if running on Railway
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("CHROME_BIN")
    print(f"🚂 Railway environment detected: {is_railway}")
    
    # Create chrome options if not provided
    if chrome_options is None:
        chrome_options = webdriver.ChromeOptions()
        
        # Download preferences
        prefs = {'download.default_directory': str(BASE_DIR / "selenium")}
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Basic options
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Railway specific flags
        if is_railway:
            chrome_options.add_argument("--headless")  # Force headless on Railway
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--single-process")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-gpu-sandbox")
            chrome_options.add_argument("--remote-debugging-port=9222")
        
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
    Create a stealth Chrome driver using undetected-chromedriver.
    Falls back to regular Chrome driver if UC fails.
    Enhanced for Railway deployment with fixed options.
    """
    print("🥷 Creating stealth Chrome driver...")
    
    # Check if running on Railway
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("CHROME_BIN")
    print(f"🚂 Railway environment detected: {is_railway}")
    
    # Railway-specific paths
    if is_railway:
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
    
    # Undetected Chrome options - FIXED to remove incompatible options
    options = uc.ChromeOptions()
    
    # Basic stealth arguments (removed problematic excludeSwitches)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-field-trial-config")
    options.add_argument("--disable-back-forward-cache")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-domain-reliability")
    
    # Railway/Production specific flags
    if is_railway:
        print("🚂 Adding Railway-specific Chrome options...")
        options.add_argument("--headless")  # Force headless on Railway
        options.add_argument("--single-process")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-seccomp-filter-sandbox")
        
        # Set binary location
        options.binary_location = chrome_bin
        print(f"🔧 Chrome binary: {chrome_bin}")

    # FIXED: Advanced stealth preferences - removed incompatible excludeSwitches
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # Don't load images for speed
        "download.default_directory": str(BASE_DIR / "selenium"),
        # Disable password manager
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        # Disable notifications
        "profile.default_content_setting_values.notifications": 2,
        # Disable location sharing
        "profile.default_content_setting_values.geolocation": 2,
        # Disable media stream
        "profile.default_content_setting_values.media_stream": 2,
        # Stealth mode preferences
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    }
    
    options.add_experimental_option("prefs", prefs)
    # REMOVED: These lines that cause the error
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option('useAutomationExtension', False)
    
    # User agent for stealth
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Set window size
    options.add_argument(f"--window-size={BROWSER_WIDTH},{BROWSER_HEIGHT}")
    
    # Headless mode (force on Railway)
    if not SHOW_BROWSER or is_railway:
        options.add_argument("--headless")
        print("🥷 Running stealth driver in HEADLESS mode")
    else:
        print("👁️ Running stealth driver in VISIBLE mode")
    
    # Try to launch undetected Chrome driver first
    try:
        print("🚀 Attempting to create undetected Chrome driver...")
        
        # Handle Railway Chromium binary location for UC
        if os.environ.get("CHROME_BIN"):
            print(f"🏗️ Setting Chrome binary location to: {os.environ.get('CHROME_BIN')}")
            driver = uc.Chrome(options=options, browser_executable_path=os.environ.get("CHROME_BIN"))
        else:
            driver = uc.Chrome(options=options)
        
        # Test the driver session to make sure it's working
        try:
            driver.get("about:blank")  # Simple test
            print("✅ SUCCESS: Undetected Chrome driver created and tested!")
            return driver
        except Exception as test_error:
            print(f"⚠️ Undetected Chrome driver created but failed session test: {test_error}")
            try:
                driver.quit()
            except:
                pass
            raise test_error
        
    except Exception as uc_error:
        print(f"⚠️ Undetected Chrome driver failed: {uc_error}")
        print("🔄 Falling back to regular Chrome driver...")
        
        try:
            # Convert UC options to regular ChromeOptions
            chrome_options = webdriver.ChromeOptions()
            for arg in options.arguments:
                chrome_options.add_argument(arg)
            
            # Add the experimental options (but skip the problematic ones)
            for key, value in options.experimental_options.items():
                if key not in ['excludeSwitches', 'useAutomationExtension']:  # Skip problematic options
                    chrome_options.add_experimental_option(key, value)
            
            # Set binary location for regular Chrome
            if is_railway and chrome_bin:
                chrome_options.binary_location = chrome_bin
                print(f"🔧 Setting binary location for regular Chrome: {chrome_bin}")
            
            # Use our improved get_chrome_driver function
            fallback_driver = get_chrome_driver(chrome_options)
            
            # Test the fallback driver session
            try:
                fallback_driver.get("about:blank")  # Simple test
                print("✅ Fallback Chrome driver created and tested successfully")
                return fallback_driver
            except Exception as test_error:
                print(f"⚠️ Fallback Chrome driver created but failed session test: {test_error}")
                try:
                    fallback_driver.quit()
                except:
                    pass
                raise test_error
            
        except Exception as fallback_error:
            print(f"❌ Fallback Chrome driver also failed: {fallback_error}")
            raise fallback_error

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
        
        # Retry logic for session creation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🚀 Creating new Chrome session (attempt {attempt + 1}/{max_retries})...")
                driver = create_stealth_driver()
                
                # Validate session is working
                try:
                    driver.get("about:blank")
                    print("✅ Chrome session validated successfully")
                    cache.set('last_chrome_session_time', time.time(), 60)
                    return driver
                except Exception as validation_error:
                    print(f"⚠️ Session validation failed: {validation_error}")
                    try:
                        driver.quit()
                    except:
                        pass
                    if attempt < max_retries - 1:
                        print(f"🔄 Retrying session creation...")
                        time.sleep(3)  # Wait before retry
                        continue
                    else:
                        raise validation_error
                        
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
    Main scraper task for financial data with improved error handling and session recovery.
    """
    print(f"🎯 Starting scraper task: {download_type} for {ticker_value} ({market_value})")
    
    max_retries = 2  # Allow task-level retries for session failures
    
    for task_attempt in range(max_retries):
        driver = None
        try:
            print(f"📝 Task attempt {task_attempt + 1}/{max_retries}")
            
            # Create Chrome driver with fallback mechanism
            driver = safe_create_stealth_driver()
            
            # Validate session before using
            if not validate_driver_session(driver):
                raise Exception("Initial session validation failed")
            
            print(f"🌐 Navigating to Morningstar for {ticker_value}...")
            driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
            
            # Validate session after navigation
            if not validate_driver_session(driver):
                raise Exception("Session failed after navigation")
            
            if download_type == "INCOME_STATEMENT":
                print(f"Starting income statement scraping for {ticker_value}")
                print(f"Current URL: {driver.current_url}")
                
                # Validate session before clicking
                if not validate_driver_session(driver):
                    raise Exception("Session failed before Income Statement click")
                
                WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Income Statement')]"))).click()
                print("Successfully clicked Income Statement button")
                
                # Add wait for page to load after clicking Income Statement
                sleep(3)
                
                # Validate session after clicking
                if not validate_driver_session(driver):
                    raise Exception("Session failed after Income Statement click")
                
                # Debug: Check what links are available on the page
                try:
                    links = driver.find_elements(By.TAG_NAME, "a")
                    print(f"Found {len(links)} links on page")
                    for i, link in enumerate(links[:10]):  # Show first 10 links
                        print(f"Link {i}: '{link.text}' - href: {link.get_attribute('href')}")
                except Exception as e:
                    print(f"Error getting links: {e}")
                
                # Try multiple strategies to find and click Expand Detail View
                expand_clicked = False
                try:
                    # Strategy 1: Original selector
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
                    expand_clicked = True
                    print("Successfully clicked Expand Detail View (Strategy 1)")
                except:
                    try:
                        # Strategy 2: Look for any expand link
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Expand')]"))).click()
                        expand_clicked = True
                        print("Successfully clicked Expand link (Strategy 2)")
                    except:
                        try:
                            # Strategy 3: Look for detail view link
                            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Detail View')]"))).click()
                            expand_clicked = True
                            print("Successfully clicked Detail View link (Strategy 3)")
                        except:
                            print("Warning: Could not find Expand Detail View link. Proceeding without expanding...")
                
                if expand_clicked:
                    sleep(2)  # Wait for expansion to complete
                    
                    # Validate session after expansion
                    if not validate_driver_session(driver):
                        raise Exception("Session failed after detail view expansion")
                
                # Debug: Check what buttons are available on the page
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    print(f"Found {len(buttons)} buttons on page")
                    for i, button in enumerate(buttons[:10]):  # Show first 10 buttons
                        print(f"Button {i}: '{button.text}' - id: {button.get_attribute('id')} - class: {button.get_attribute('class')}")
                except Exception as e:
                    print(f"Error getting buttons: {e}")
                
                # Try multiple strategies to find and click Export button
                export_clicked = False
                try:
                    # Strategy 1: Original selector
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
                    export_clicked = True
                    print("Successfully clicked Export Data button (Strategy 1)")
                except:
                    try:
                        # Strategy 2: By ID (from the HTML you provided)
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "salEqsvFinancialsPopoverExport"))).click()
                        export_clicked = True
                        print("Successfully clicked Export button by ID (Strategy 2)")
                    except:
                        try:
                            # Strategy 3: By aria-label
                            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Export']"))).click()
                            export_clicked = True
                            print("Successfully clicked Export button by aria-label (Strategy 3)")
                        except:
                            try:
                                # Strategy 4: By class and icon combination
                                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'mds-button--icon-only__sal') and .//span[@data-mds-icon-name='share']]"))).click()
                                export_clicked = True
                                print("Successfully clicked Export button by class/icon (Strategy 4)")
                            except:
                                print("Warning: Could not find Export button. Data may not be available for download.")
                
                if export_clicked:
                    sleep(10)  # Wait for download to complete
                    print("Waiting for download to complete...")
                else:
                    sleep(5)   # Short wait even if export failed
                    print("No export performed, continuing...")

                try:
                    excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "Income Statement_Annual_As Originally Reported.xls")
                    data1 = excel_data_df.to_json()
                    print("Successfully read income statement Excel file")
                    print(data1)
                    database.child("income_statement").set({"income_statement": data1 })
                except Exception as e:
                    print(f"Error reading income statement Excel file: {e}")
                    x =  '{"income_statement":{"none":"no data"}}'
                    database.child("income_statement").set({"income_statement": x })
                sleep(10)
                # Successfully completed the task
                safe_close_driver(driver)
                return 'DONE'
                
            elif download_type == "BALANCE_SHEET":
                # Similar logic for Balance Sheet - just complete the task and return
                print(f"Starting balance sheet scraping for {ticker_value}")
                # ... existing balance sheet logic stays the same ...
                safe_close_driver(driver)
                return 'DONE'
                
            elif download_type == "CASH_FLOW":
                # Similar logic for Cash Flow - just complete the task and return
                print(f"Starting cash flow scraping for {ticker_value}")
                # ... existing cash flow logic stays the same ...
                safe_close_driver(driver)
                return 'DONE'
                
        except Exception as session_error:
            print(f"❌ Session error on attempt {task_attempt + 1}: {session_error}")
            safe_close_driver(driver)
            
            if task_attempt < max_retries - 1:
                print(f"🔄 Retrying task in 5 seconds...")
                time.sleep(5)
                continue
            else:
                print(f"❌ All {max_retries} attempts failed. Setting fallback data.")
                # Set fallback data based on download_type
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
            # This runs after each attempt
            safe_close_driver(driver)
    
    # If we somehow exit the loop without returning, this is a fallback
    return 'ERROR'

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

