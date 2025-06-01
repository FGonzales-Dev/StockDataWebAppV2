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

def get_chrome_driver(chrome_options=None):
    """
    Create Chrome WebDriver with automatic environment detection.
    Uses CHROMEDRIVER_PATH environment variable for production,
    local chromedriver path for development, with WebDriverManager as fallback.
    """
    CHROME_DRIVER_PATH = BASE_DIR + "/chromedriver"
    
    # Create chrome options if not provided
    if chrome_options is None:
        chrome_options = webdriver.ChromeOptions()
        
        # Download preferences
        prefs = {'download.default_directory': BASE_DIR + DOWNLOAD_DIRECTORY}
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Basic options
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-dev-shm-usage")
        
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
    
    if os.environ.get("CHROMEDRIVER_PATH"):
        # Production environment (Heroku, etc.)
        return webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    elif os.path.exists(CHROME_DRIVER_PATH):
        # Local development environment with local chromedriver
        return webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chrome_options)
    else:
        # Fallback: Use WebDriverManager to auto-download compatible ChromeDriver
        return webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=chrome_options)

def format_dict(d):
    vals = list(d.values())
    return "={},".join(d.keys()).format(*vals) + "={}".format(vals[-1])



# Testing: Adding options to undetected chrome driver
def create_stealth_driver():
    options = uc.ChromeOptions()
    
    # Detect environment
    IS_FLY = os.environ.get('FLY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
    IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT')
    IS_PRODUCTION = IS_FLY or IS_RAILWAY
    
    # Container-specific Chrome options for production deployment
    if IS_PRODUCTION:
        print(f"🚀 Production environment detected: {'Fly.io' if IS_FLY else 'Railway' if IS_RAILWAY else 'Unknown'}")
        # Essential container flags
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI,VizDisplayCompositor")
        options.add_argument("--headless=new")  # Modern headless mode
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        
        # Memory and stability optimization for containers  
        options.add_argument("--memory-pressure-off")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--mute-audio")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        # Resource limits
        if IS_FLY:
            options.add_argument("--max_old_space_size=1024")  # 1GB for Fly.io
        else:
            options.add_argument("--max_old_space_size=512")   # 512MB for Railway
        
        # Shared memory size
        options.add_argument("--shm-size=1gb")
        
        print("🔧 Applied production Chrome options for container deployment")
    else:
        print("💻 Development environment - using standard options")
        # Standard options for development
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    
    # Set window size to common screen resolution
    options.add_argument("--window-size=1920,1080")

    # Set a random realistic user-agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")

    # Anti-bot arguments
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")

    # Download preferences (but keep images and JavaScript enabled for proper scraping)
    prefs = {
        "download.default_directory": BASE_DIR + DOWNLOAD_DIRECTORY,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0
    }
    options.add_experimental_option("prefs", prefs)

    # Run headless in production
    if IS_PRODUCTION:
        options.headless = True
    else:
        options.headless = not SHOW_BROWSER

    # Launch driver with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🚀 Creating Chrome driver (attempt {attempt + 1}/{max_retries})...")
            driver = uc.Chrome(options=options)
            print("✅ Chrome driver created successfully!")
            
            # Set page load timeout
            driver.set_page_load_timeout(60)
            
            # Optional: Stealth tweaks inside browser (only if not in production to avoid JS errors)
            if not IS_PRODUCTION:
                driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {
                        "source": """
                            Object.defineProperty(navigator, 'webdriver', {
                              get: () => undefined
                            });
                            window.navigator.chrome = {
                              runtime: {},
                            };
                            Object.defineProperty(navigator, 'plugins', {
                              get: () => [1, 2, 3],
                            });
                            Object.defineProperty(navigator, 'languages', {
                              get: () => ['en-US', 'en'],
                            });
                        """
                    },
                )
            
            return driver
            
        except Exception as e:
            print(f"❌ Error creating Chrome driver (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise e
            else:
                print(f"🔄 Retrying in 2 seconds...")
                sleep(2)


@shared_task(bind=True)
def scraper(self,ticker_value,market_value,download_type):
    # Create Chrome driver with automatic configuration
    # driver = get_chrome_driver()
    
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")

    driver = create_stealth_driver()
    try:
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
                excel_data_df = pd.read_excel(BASE_DIR + DOWNLOAD_DIRECTORY + "/Income Statement_Annual_As Originally Reported.xls")
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
                excel_data_df = pd.read_excel(BASE_DIR + DOWNLOAD_DIRECTORY + "/Balance Sheet_Annual_As Originally Reported.xls")
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
                excel_data_df = pd.read_excel(BASE_DIR + DOWNLOAD_DIRECTORY + "/Cash Flow_Annual_As Originally Reported.xls")
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
        driver.quit()

@shared_task(bind=True)
def scraper_dividends(self, ticker_value, market_value):
    # Create Chrome driver with stealth configuration (same as scraper function)
    driver_dividends = create_stealth_driver()
    
    try:
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
        print(f"Error in scraper_dividends: {e}")
        x = '{"dividends":{"none":"no data"}}'
        database.child("dividends").set({"dividends": x})
        return 'ERROR'
    finally:
        driver_dividends.quit()

@shared_task()
def scraper_valuation(ticker_value,market_value,download_type):
    # Create Chrome driver with stealth configuration (same as scraper_dividends)
    valuation_driver = create_stealth_driver()
    
    try:
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
                    excel_data_df = pd.read_excel(BASE_DIR + DOWNLOAD_DIRECTORY + "/cashFlow.xls")
                    data1 = excel_data_df.to_json()
                    print("Successfully read cash flow valuation Excel file")
                    print(data1)
                    database.child("valuation_cash_flow").set({"valuation_cash_flow": data1})
                elif download_type == "VALUATION_GROWTH":
                    excel_data_df = pd.read_excel(BASE_DIR + DOWNLOAD_DIRECTORY + "/growthTable.xls")
                    data1 = excel_data_df.to_json()
                    print("Successfully read growth valuation Excel file")
                    print(data1)
                    database.child("valuation_growth").set({"valuation_growth": data1})
                elif download_type == "VALUATION_FINANCIAL_HEALTH":
                    excel_data_df = pd.read_excel(BASE_DIR + DOWNLOAD_DIRECTORY + "/financialHealth.xls")
                    data1 = excel_data_df.to_json()
                    print("Successfully read financial health valuation Excel file")
                    print(data1)
                    database.child("valuation_financial_health").set({"valuation_financial_health": data1})
                elif download_type == "VALUATION_OPERATING_EFFICIENCY":
                    excel_data_df = pd.read_excel(BASE_DIR + DOWNLOAD_DIRECTORY + "/operatingAndEfficiency.xls")
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
        print(f"Error in scraper_valuation: {e}")
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
        valuation_driver.quit()

@shared_task(bind=True)
def all_scraper(self,ticker_value,market_value):
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
        excel_data_df = pd.read_excel(BASE_DIR + "/selenium/financialHealth.xls")
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
        excel_data_df = pd.read_excel(BASE_DIR + "/selenium/operatingAndEfficiency.xls")
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
        excel_data_df = pd.read_excel(BASE_DIR + "/selenium/cashFlow.xls")
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
        excel_data_df = pd.read_excel(BASE_DIR + "/selenium/growthTable.xls")
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
        excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Income Statement_Annual_As Originally Reported.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("income_statement").set({"income_statement": data1 })
    except:
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
            excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Balance Sheet_Annual_As Originally Reported.xls")
            data1 = excel_data_df.to_json()
            print(data1)
            database.child("balance_sheet").set({"balance_sheet": data1 })
    except:
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
        excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Cash Flow_Annual_As Originally Reported.xls")
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

