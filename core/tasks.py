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
    
    try:
        # Detect Chrome installation based on environment
        chrome_candidates = []
        
        if os.environ.get("CHROME_BIN"):
            # Production environment (Railway)
            chrome_candidates.append(os.environ.get("CHROME_BIN"))
        
        # Add platform-specific Chrome paths
        system = platform.system().lower()
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
        
        # Find working Chrome executable
        chrome_bin = None
        for candidate in chrome_candidates:
            try:
                # Test if this Chrome path works
                result = subprocess.run([candidate, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    chrome_bin = candidate
                    print(f"✅ Found Chrome at: {chrome_bin}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                continue
        
        if not chrome_bin:
            raise Exception("No Chrome installation found. Please install Google Chrome or Chromium.")
        
        # Get Chrome version
        result = subprocess.run([chrome_bin, "--version"], capture_output=True, text=True)
        chrome_version = result.stdout.strip().split()[-1]
        print(f"🔍 Detected Chrome version: {chrome_version}")
        
        # Determine platform for download
        machine = platform.machine().lower()
        
        if system == "linux":
            if "arm" in machine or "aarch64" in machine:
                platform_name = "linux64"  # No ARM builds available, use x64
            else:
                platform_name = "linux64"
        elif system == "darwin":
            if "arm" in machine or machine == "arm64":
                platform_name = "mac-arm64"
            else:
                platform_name = "mac-x64"
        elif system == "windows":
            platform_name = "win64" if "64" in machine else "win32"
        else:
            platform_name = "linux64"  # Default fallback
        
        # Download URL using Chrome for Testing API
        url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/{platform_name}/chromedriver-{platform_name}.zip"
        print(f"📥 Downloading ChromeDriver from: {url}")
        
        # Download ChromeDriver
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Failed to download ChromeDriver: HTTP {response.status_code}")
        
        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "chromedriver.zip")
            with open(zip_path, "wb") as f:
                f.write(response.content)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the chromedriver executable
            chromedriver_name = "chromedriver.exe" if system == "windows" else "chromedriver"
            
            # Look for chromedriver in extracted directories
            for root, dirs, files in os.walk(temp_dir):
                if chromedriver_name in files:
                    src_path = os.path.join(root, chromedriver_name)
                    
                    # Copy to a permanent location
                    dest_dir = BASE_DIR / "drivers"
                    dest_dir.mkdir(exist_ok=True)
                    dest_path = dest_dir / chromedriver_name
                    
                    import shutil
                    shutil.copy2(src_path, dest_path)
                    os.chmod(dest_path, 0o755)
                    
                    print(f"✅ ChromeDriver installed to: {dest_path}")
                    return str(dest_path)
        
        raise Exception("ChromeDriver executable not found in downloaded archive")
        
    except Exception as e:
        print(f"⚠️ Chrome for Testing download failed: {e}")
        return None


def get_chrome_driver(chrome_options=None):
    """
    Create Chrome WebDriver with automatic environment detection.
    Uses Chrome for Testing API for the most reliable compatibility.
    """
    CHROME_DRIVER_PATH = BASE_DIR / "chromedriver"
    
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
        
        # Railway/Production specific flags
        if os.environ.get("CHROME_BIN"):
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--single-process")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
        
        # Window size
        chrome_options.add_argument(f"--window-size={BROWSER_WIDTH},{BROWSER_HEIGHT}")
        
        # User agent
        chrome_options.add_argument(f"user-agent={USER_AGENT}")
        
        # Headless mode based on configuration
        if not SHOW_BROWSER:
            chrome_options.add_argument("--headless")
            print("🔍 Running in HEADLESS mode (browser hidden)")
        else:
            chrome_options.add_argument("--start-maximized")
            print("👁️ Running in VISIBLE mode (browser will be shown)")
    
    # Set Chrome binary location if in production environment
    if os.environ.get("CHROME_BIN"):
        chrome_options.binary_location = os.environ.get("CHROME_BIN")
        print(f"🏗️ Chrome binary location: {os.environ.get('CHROME_BIN')}")
    
    # Priority 1: Use Chrome for Testing API (most reliable for exact compatibility)
    try:
        driver_path = get_chrome_for_testing_driver()
        if driver_path and os.path.exists(driver_path):
            print(f"🎯 Using Chrome for Testing ChromeDriver: {driver_path}")
            return webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    except Exception as cft_error:
        print(f"⚠️ Chrome for Testing failed: {cft_error}")
    
    # Priority 2: Use WebDriverManager (fallback for local development)
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        print(f"📦 Using WebDriverManager ChromeDriver: {driver_path}")
        return webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    except Exception as wdm_error:
        print(f"⚠️ WebDriverManager failed: {wdm_error}")
        
        # Priority 3: Try system-installed ChromeDriver (from nixpacks) with error logging
        if os.environ.get("CHROMEDRIVER_PATH") and os.path.exists(os.environ.get("CHROMEDRIVER_PATH")):
            try:
                print(f"🔄 Trying system ChromeDriver: {os.environ.get('CHROMEDRIVER_PATH')}")
                
                # Test ChromeDriver version compatibility first
                import subprocess
                result = subprocess.run([os.environ.get("CHROMEDRIVER_PATH"), "--version"], 
                                     capture_output=True, text=True, timeout=10)
                print(f"ChromeDriver version: {result.stdout}")
                
                return webdriver.Chrome(
                    executable_path=os.environ.get("CHROMEDRIVER_PATH"), 
                    options=chrome_options
                )
            except Exception as system_error:
                print(f"⚠️ System ChromeDriver failed: {system_error}")
        
        # Priority 4: Try local development ChromeDriver
        if os.path.exists(CHROME_DRIVER_PATH):
            try:
                print("🏠 Trying local development ChromeDriver")
                return webdriver.Chrome(
                    executable_path=str(CHROME_DRIVER_PATH), 
                    options=chrome_options
                )
            except Exception as local_error:
                print(f"⚠️ Local ChromeDriver failed: {local_error}")
        
        # Priority 5: Use Chrome's built-in DevTools (emergency fallback)
        try:
            print("🆘 Attempting Chrome with remote debugging (emergency fallback)")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor,VizHitTestSurfaceLayer")
            
            # Try without specifying executable_path (let Selenium find it)
            return webdriver.Chrome(options=chrome_options)
            
        except Exception as emergency_error:
            print(f"❌ All ChromeDriver methods failed. Last error: {emergency_error}")
            raise Exception(f"Could not create Chrome driver. CfT: Chrome for Testing failed, WDM: {wdm_error}, Emergency: {emergency_error}")

def format_dict(d):
    vals = list(d.values())
    return "={},".join(d.keys()).format(*vals) + "={}".format(vals[-1])



# Testing: Adding options to undetected chrome driver
def create_stealth_driver():
    """
    Create a stealth Chrome driver using undetected-chromedriver.
    Falls back to regular Chrome driver if UC fails.
    """
    print("🥷 Creating stealth Chrome driver...")
    
    # Undetected Chrome options
    options = uc.ChromeOptions()
    
    # Basic stealth arguments
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
    if os.environ.get("CHROME_BIN"):
        options.add_argument("--single-process")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")

    # Advanced stealth preferences
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
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.media_stream": 2,
        # Disable automation indicators
        "excludeSwitches": ["enable-automation"],
        "useAutomationExtension": False
    }
    
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent for stealth
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Set window size
    options.add_argument(f"--window-size={BROWSER_WIDTH},{BROWSER_HEIGHT}")
    
    # Headless mode
    if not SHOW_BROWSER:
        options.add_argument("--headless")
        print("🥷 Running stealth driver in HEADLESS mode")
    else:
        print("👁️ Running stealth driver in VISIBLE mode")
    
    try:
        # Set Chrome binary if available
        chrome_bin = os.environ.get("CHROME_BIN")
        if chrome_bin:
            print(f"🔧 Using Chrome binary: {chrome_bin}")
            
        # Try creating UC driver with explicit paths if available
        driver_kwargs = {"options": options}
        
        if chrome_bin:
            driver_kwargs["browser_executable_path"] = chrome_bin
            
        # Try system ChromeDriver first
        if os.environ.get("CHROMEDRIVER_PATH") and os.path.exists(os.environ.get("CHROMEDRIVER_PATH")):
            driver_kwargs["driver_executable_path"] = os.environ.get("CHROMEDRIVER_PATH")
            print(f"🎯 Using system ChromeDriver for UC: {os.environ.get('CHROMEDRIVER_PATH')}")
        
        driver = uc.Chrome(**driver_kwargs)
        
        # Inject stealth JavaScript to hide automation
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        driver.execute_script("""
            window.navigator.chrome = {
                runtime: {},
            };
        """)
        
        driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        print("✅ Stealth driver created successfully with undetected-chromedriver")
        return driver
        
    except Exception as uc_error:
        print(f"⚠️ Undetected Chrome driver failed: {uc_error}")
        print("🔄 Falling back to regular Chrome driver...")
        
        try:
            # Convert UC options to regular ChromeOptions
            chrome_options = webdriver.ChromeOptions()
            for arg in options.arguments:
                chrome_options.add_argument(arg)
            
            # Add the experimental options
            for key, value in options.experimental_options.items():
                chrome_options.add_experimental_option(key, value)
            
            # Use our improved get_chrome_driver function
            fallback_driver = get_chrome_driver(chrome_options)
            
            # Inject the same stealth JavaScript
            fallback_driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            print("✅ Fallback Chrome driver created successfully")
            return fallback_driver
            
        except Exception as fallback_error:
            print(f"❌ Fallback Chrome driver also failed: {fallback_error}")
            raise fallback_error


@shared_task(bind=True)
def scraper(self,ticker_value,market_value,download_type):
    """
    Main scraper task for financial data with improved error handling.
    """
    print(f"🎯 Starting scraper task: {download_type} for {ticker_value} ({market_value})")
    
    driver = None
    try:
        # Create Chrome driver with fallback mechanism
        driver = create_stealth_driver()
        driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
        if download_type == "INCOME_STATEMENT":
            print(f"Starting income statement scraping for {ticker_value}")
            print(f"Current URL: {driver.current_url}")
            
            WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Income Statement')]"))).click()
            print("Successfully clicked Income Statement button")
            
            # Add wait for page to load after clicking Income Statement
            sleep(3)
            
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
            return 'DONE'
        elif download_type == "BALANCE_SHEET":
            print(f"Starting balance sheet scraping for {ticker_value}")
            print(f"Current URL: {driver.current_url}")
            
            WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Balance Sheet')]"))).click()
            print("Successfully clicked Balance Sheet button")
            
            # Add wait for page to load after clicking Balance Sheet
            sleep(3)
            
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
                excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "Balance Sheet_Annual_As Originally Reported.xls")
                data1 = excel_data_df.to_json()
                print("Successfully read balance sheet Excel file")
                print(data1)
                database.child("balance_sheet").set({"balance_sheet": data1 })
            except Exception as e:
                print(f"Error reading balance sheet Excel file: {e}")
                x =  '{"balance_sheet":{"none":"no data"}}'
                database.child("balance_sheet").set({"balance_sheet": x })
            sleep(10)
            return 'DONE'
        elif download_type == "CASH_FLOW":
            print(f"Starting cash flow scraping for {ticker_value}")
            print(f"Current URL: {driver.current_url}")
            
            WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
            print("Successfully clicked Cash Flow button")
            
            # Add wait for page to load after clicking Cash Flow
            sleep(3)
            
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
                excel_data_df = pd.read_excel(BASE_DIR / "selenium" / "Cash Flow_Annual_As Originally Reported.xls")
                data1 = excel_data_df.to_json()
                print("Successfully read cash flow Excel file")
                print(data1)
                database.child("cash_flow").set({"cash_flow": data1 })
            except Exception as e:
                print(f"Error reading cash flow Excel file: {e}")
                x =  '{"cash_flow":{"none":"no data"}}'
                database.child("cash_flow").set({"cash_flow": x })
            sleep(10)
            return 'DONE'
    finally:
        if driver:
            try:
                driver.quit()
                print("🔄 Driver closed successfully")
            except Exception as e:
                print(f"Warning: Error closing driver: {e}")

@shared_task(bind=True)
def scraper_dividends(self, ticker_value, market_value):
    """
    Scraper task for dividends data with improved error handling.
    """
    print(f"🎯 Starting dividends scraper for {ticker_value} ({market_value})")
    
    driver_dividends = None
    try:
        # Create Chrome driver with fallback mechanism (same as scraper function)
        driver_dividends = create_stealth_driver()
        
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
        if driver_dividends:
            try:
                driver_dividends.quit()
                print("🔄 Driver closed successfully")
            except Exception as e:
                print(f"Warning: Error closing driver: {e}")

@shared_task()
def scraper_valuation(ticker_value,market_value,download_type):
    """
    Scraper task for valuation data with improved error handling.
    """
    print(f"🎯 Starting valuation scraper: {download_type} for {ticker_value} ({market_value})")
    
    valuation_driver = None
    try:
        # Create Chrome driver with fallback mechanism (same as scraper_dividends)
        valuation_driver = create_stealth_driver()
        
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
        if valuation_driver:
            try:
                valuation_driver.quit()
                print("🔄 Driver closed successfully")
            except Exception as e:
                print(f"Warning: Error closing driver: {e}")

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

