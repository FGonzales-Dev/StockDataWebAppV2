"""
Firestore-based Celery Tasks for Stock Data Scraping
Check Firestore first, scrape only if data doesn't exist
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from celery import shared_task
from celery_progress.backend import ProgressRecorder
import pandas as pd
from time import sleep
import os
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from stock_scraper.settings import BASE_DIR
from .firestore_storage import (
    FirestoreStorage, 
    DataType, 
    check_existing_data, 
    store_scraped_data,
    get_storage
)
import uuid
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapingConfig:
    """Configuration for scraping operations"""
    show_browser: bool = True
    element_wait_timeout: int = 30
    download_directory: str = "/selenium"
    browser_width: int = 1920
    browser_height: int = 1080
    max_retries: int = 3

class OptimizedScrapingStrategy:
    """Optimized base scraping strategy with Firestore storage"""
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.driver = None
        self.storage = get_storage()
    
    def create_driver(self):
        """Create optimized Chrome driver"""
        # Set Chrome options
        options = uc.ChromeOptions()
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument(f"--window-size={self.config.browser_width},{self.config.browser_height}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-data-dir=/tmp/{uuid.uuid4()}")
        options.add_argument("--lang=en-US")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--no-first-run")
        options.add_argument("--test-type")
        options.add_argument("--start-maximized")
        options.add_argument("--log-level=0")
        options.add_argument("--headless")  # Explicitly set headless mode
        options.add_argument("--disable-gpu")  # Disable GPU for headless mode in Docker
         
         # Initialize driver with retry mechanism
        max_retries = 5  # Increased retries
        for attempt in range(max_retries):
            try:
                self.driver = uc.Chrome(
                    options=options,
                    headless=True,  # Enforce headless mode
                    version_main=137  # Match the installed Chrome major version
                )
                logger.info("Chrome driver initialized successfully")
                return self.driver  # Return the driver for explicit assignment if needed
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to initialize Chrome: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("All retries failed to initialize Chrome driver")
                    raise
                time.sleep(5)  # Increased wait time before retrying
    
    def safe_click(self, selectors: List[str], timeout: int = 10) -> bool:
        """Safely click an element using multiple selectors"""
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                element.click()
                logger.info(f"Successfully clicked using selector: {selector}")
                return True
            except TimeoutException:
                continue
        logger.warning("All click selectors failed")
        return False
    
    def find_element_safely(self, selectors: List[str], timeout: int = 10):
        """Find an element using multiple selectors"""
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((By.XPATH, selector))
                )
                logger.info(f"Successfully found element using selector: {selector}")
                return element
            except TimeoutException:
                continue
        logger.warning("All find selectors failed")
        return None
    
    def check_existing_data_first(self, ticker: str, market: str, data_type: DataType) -> Optional[str]:
        """Check if data already exists in Firestore"""
        return check_existing_data(ticker, market, data_type)
    
    def store_data(self, ticker: str, market: str, data_type: DataType, data: str, status: str = 'DONE'):
        """Store data in Firestore"""
        success = store_scraped_data(ticker, market, data_type, data, status)
        if success:
            logger.info(f"Stored {data_type.value} data for {ticker} {market}")
        else:
            logger.error(f"Failed to store {data_type.value} data for {ticker} {market}")
    
    def store_fallback_data(self, ticker: str, market: str, data_type: DataType):
        """Store fallback data when scraping fails"""
        fallback = json.dumps({data_type.value.lower(): {"none": "no data"}})
        self.store_data(ticker, market, data_type, fallback, 'ERROR')


@shared_task(bind=True)
def financial_statement_firestore_check(self, ticker_value: str, market_value: str, download_type: str):
    """
    Main scraper task with Firestore check-first approach
    """
    try:
        data_type = DataType(download_type)
        
        if data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
            result = scraper_financial_statement(ticker_value, market_value, data_type)
            
            # Update progress
            if result == 'EXISTING':
                self.update_state(state='SUCCESS', meta={'status': 'Data already exists - retrieved from storage'})
            elif result == 'DONE':
                self.update_state(state='SUCCESS', meta={'status': 'Data scraped and stored successfully'})
            else:
                self.update_state(state='FAILURE', meta={'status': f'Scraping failed: {result}'})
            
            return result
        else:
            logger.error(f"Data type {download_type} not yet implemented for Firestore")
            return 'ERROR'
            
    except ValueError:
        logger.error(f"Invalid data type: {download_type}")
        return 'ERROR'
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return 'ERROR'
    
@shared_task(bind=True)
def key_metrics_firestore_check(self, ticker_value: str, market_value: str, download_type: str):
    """
    Main scraper task with Firestore check-first approach
    """
    try:
        data_type = DataType(download_type)
        
        if data_type in [DataType.KEY_METRICS_CASH_FLOW, DataType.KEY_METRICS_GROWTH, DataType.KEY_METRICS_FINANCIAL_HEALTH]:
            result = scraper_key_metrics(ticker_value, market_value, data_type)
            
            # Update progress
            if result == 'EXISTING':
                self.update_state(state='SUCCESS', meta={'status': 'Data already exists - retrieved from storage'})
            elif result == 'DONE':
                self.update_state(state='SUCCESS', meta={'status': 'Data scraped and stored successfully'})
            else:
                self.update_state(state='FAILURE', meta={'status': f'Scraping failed: {result}'})
            
            return result
        else:
            logger.error(f"Data type {download_type} not yet implemented for Firestore")
            return 'ERROR'
            
    except ValueError:
        logger.error(f"Invalid data type: {download_type}")
        return 'ERROR'
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return 'ERROR'




def scraper_financial_statement(ticker: str, market: str, data_type: DataType) -> str:
    """
    Financial statement scraper with Firestore check-first approach
    Returns: 'EXISTING' if data found, 'DONE' if scraped successfully, 'ERROR' if failed
    """
    strategy = OptimizedScrapingStrategy()
    
    # STEP 1: Check if data already exists
    existing_data = strategy.check_existing_data_first(ticker, market, data_type)
    if existing_data:
        logger.info(f"Found existing {data_type.value} data for {ticker} {market} - skipping scrape")
        return 'EXISTING'
    
    # STEP 2: Data doesn't exist, proceed with scraping
    logger.info(f"No existing data found for {ticker} {market} {data_type.value} - starting scrape")
    
    driver = None
    try:
        driver = strategy.create_driver()
        if driver is None:
            logger.error("Driver initialization returned None, cannot proceed with scraping")
            raise Exception("Chrome driver is None after initialization")
        strategy.driver = driver
        
        # Ensure download directory exists
        download_dir = BASE_DIR + strategy.config.download_directory
        if not os.path.exists(download_dir):
            logger.info(f"Creating download directory at {download_dir}")
            os.makedirs(download_dir, exist_ok=True)
        else:
            logger.info(f"Download directory already exists at {download_dir}")
        
        url = f"https://www.morningstar.com/stocks/{market}/{ticker}/financials"
        logger.info(f"Navigating to {url}")
        driver.get(url)
        
        # Click tab
        tab_text = data_type.value.replace('_', ' ').title()
        tab_selectors = [f"//button[contains(., '{tab_text}')]"]
        
        if not strategy.safe_click(tab_selectors, 30):
            raise Exception(f"Failed to click {tab_text} tab")
        
        sleep(3)
        
        export_selectors = [
            "//button[contains(., 'Export Data')]",
            "//button[@id='salEqsvFinancialsPopoverExport']"
        ]
        
        if strategy.safe_click(export_selectors):
            sleep(20)  # Increased wait time for download to complete
            
            # Process file
            filename_base_map = {
                DataType.INCOME_STATEMENT: "Income Statement_Annual_As Originally Reported",
                DataType.BALANCE_SHEET: "Balance Sheet_Annual_As Originally Reported",
                DataType.CASH_FLOW: "Cash Flow_Annual_As Originally Reported"
            }
            filename_base = filename_base_map[data_type]
            download_dir = "/root/Downloads"
            logger.info(f"Checking for downloaded file in: {download_dir} with base name: {filename_base}")
            
            max_wait = 30  # Wait up to 30 seconds for file to appear
            wait_interval = 5
            file_path = None
            for _ in range(max_wait // wait_interval):
                # Look for files matching the base name, including possible duplicates like (1), (2), etc.
                import glob
                possible_files = glob.glob(f"{download_dir}/{filename_base}*.xls")
                if possible_files:
                    # Sort by modification time, newest first
                    possible_files.sort(key=os.path.getmtime, reverse=True)
                    file_path = possible_files[0]  # Take the most recent file
                    logger.info(f"File found at {file_path}, processing Excel data")
                    try:
                        df = pd.read_excel(file_path)
                        data_json = df.to_json()
                        logger.info(f"Excel data converted to JSON, length: {len(data_json)} characters")
                        strategy.store_data(ticker, market, data_type, data_json, 'DONE')
                        logger.info(f"Data stored for {ticker} {market} {data_type.value}")
                        os.remove(file_path) 
                        return 'DONE'
                    except Exception as e:
                        logger.error(f"Error processing Excel file: {str(e)}")
                        break
                else:
                    logger.info(f"File not found yet in {download_dir} with base name {filename_base}, waiting...")
                    sleep(wait_interval)
            
            logger.warning(f"File not found in {download_dir} after waiting, falling back to placeholder data")
        
        strategy.store_fallback_data(ticker, market, data_type)
        logger.info(f"Stored fallback data for {ticker} {market} {data_type.value} due to download failure")
        return 'PARTIAL'
        
    except Exception as e:
        logger.error(f"Error: {e}")
        strategy.store_fallback_data(ticker, market, data_type)
        return 'ERROR'
    finally:
             if driver:
                 try:
                     driver.quit()
                     logger.info("Chrome driver closed successfully")
                 except Exception as e:
                     logger.error(f"Failed to close Chrome driver: {str(e)}")

def scraper_key_metrics(self, ticker: str, market_value: str, data_type: DataType) -> str:
    """Key metrics scraper with Firestore check-first approach"""
    
    strategy = OptimizedScrapingStrategy()
    
   
    # STEP 1: Check if data already exists
    existing_data = strategy.check_existing_data_first(ticker, market_value, data_type)
    if existing_data:
        logger.info(f"Found existing {data_type.value} data for {ticker} {market_value} - skipping scrape")
        return 'EXISTING'
    
    # STEP 2: Data doesn't exist, proceed with scraping
    logger.info(f"No existing data found for {ticker} {market_value} {data_type.value} - starting scrape")
    
    driver = None
    try:
            driver = strategy.create_driver()
            if driver is None:
                logger.error("Driver initialization returned None, cannot proceed with scraping")
                raise Exception("Chrome driver is None after initialization")
            strategy.driver = driver
            
            # Ensure download directory exists
            download_dir = BASE_DIR + strategy.config.download_directory
            if not os.path.exists(download_dir):
                logger.info(f"Creating download directory at {download_dir}")
                os.makedirs(download_dir, exist_ok=True)
            else:
                logger.info(f"Download directory already exists at {download_dir}")
            
            url = f"https://www.morningstar.com/stocks/{market_value}/{ticker}/key-metrics"
            logger.info(f"Navigating to {url}")
            driver.get(url)
            
            # Click appropriate tab
            if not _click_key_metrics_tab(strategy, data_type):
                logger.warning(f"Failed to click tab for {data_type.value}")
                raise Exception(f"Failed to click tab for {data_type.value}")
            
            sleep(3)
            
            # Click Export Data button
            export_selectors = [
                "//button[@id='salEqsvFinancialsPopoverExport']",
                "//button[@aria-label='Export']",
                "//div[@class='sal-financials__exportSection']//button",
                "//button[contains(@class, 'mds-button--icon-only__sal')]",
                "//button[contains(., 'Export Data')]",
                "//button[contains(@class, 'export')]"
            ]
            
            if strategy.safe_click(export_selectors):
                sleep(20)  # Increased wait time for download to complete
                
                # Process file
                filename_base_map = {
                    DataType.KEY_METRICS_CASH_FLOW: "cashFlow",
                    DataType.KEY_METRICS_GROWTH: "growthTable",
                    DataType.KEY_METRICS_FINANCIAL_HEALTH: "financialHealth"
                }
                filename_base = filename_base_map.get(data_type, "keyMetrics")
                download_dir = "/root/Downloads"
                logger.info(f"Checking for downloaded file in: {download_dir} with base name: {filename_base}")
                
                max_wait = 30  # Wait up to 30 seconds for file to appear
                wait_interval = 5
                file_path = None
                for _ in range(max_wait // wait_interval):
                    # Look for files matching the base name, including possible duplicates like (1), (2), etc.
                    import glob
                    possible_files = glob.glob(f"{download_dir}/{filename_base}*.xls")
                    if possible_files:
                        # Sort by modification time, newest first
                        possible_files.sort(key=os.path.getmtime, reverse=True)
                        file_path = possible_files[0]  # Take the most recent file
                        logger.info(f"File found at {file_path}, processing Excel data")
                        try:
                            df = pd.read_excel(file_path)
                            data_json = df.to_json()
                            logger.info(f"Excel data converted to JSON, length: {len(data_json)} characters")
                            strategy.store_data(ticker, market_value, data_type, data_json, 'DONE')
                            logger.info(f"Data stored for {ticker} {market_value} {data_type.value}")
                            os.remove(file_path) 
                            return 'DONE'
                        except Exception as e:
                            logger.error(f"Error processing Excel file: {str(e)}")
                            break
                    else:
                        logger.info(f"File not found yet in {download_dir} with base name {filename_base}, waiting...")
                        sleep(wait_interval)
                
                logger.warning(f"File not found in {download_dir} after waiting, falling back to placeholder data")
            
            strategy.store_fallback_data(ticker, market_value, data_type)
            logger.info(f"Stored fallback data for {ticker} {market_value} {data_type.value} due to download failure")
            return 'PARTIAL'
            
    except Exception as e:
            logger.error(f"Error in key metrics scraping: {e}")
            strategy.store_fallback_data(ticker, market_value, data_type)
            return 'ERROR'
    finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("Chrome driver closed successfully")
                except Exception as e:
                    logger.error(f"Failed to close Chrome driver: {str(e)}")



@shared_task(bind=True)
def scraper_dividends_firestore(self, ticker_value: str, market_value: str):
    """Dividends scraper with Firestore check-first approach"""
    strategy = OptimizedScrapingStrategy()
    data_type = DataType.DIVIDENDS
    
    # Check existing data first
    existing_data = strategy.check_existing_data_first(ticker_value, market_value, data_type)
    if existing_data:
        logger.info(f"Found existing dividends data for {ticker_value} {market_value}")
        self.update_state(state='SUCCESS', meta={'status': 'Data already exists - retrieved from storage'})
        return 'EXISTING'
    
    # Proceed with scraping
    driver = None
    try:
        driver = strategy.create_driver()
        strategy.driver = driver
        
        url = f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/dividends"
        driver.get(url)
        logger.info(f"Navigating to {url}")
        
        table_selectors = [
            "//div[@class='mds-table__scroller__sal']",
            "//div[contains(@class, 'table__scroller')]",
            "//div[contains(@class, 'table') and contains(@class, 'scroller')]",
            "//table"
        ]
        
        table_element = strategy.find_element_safely(table_selectors, 30)
        if table_element:
            data = table_element.get_attribute("outerHTML")
            df = pd.read_html(data)
            if df and len(df) > 0:
                data_json = df[0].to_json()
                strategy.store_data(ticker_value, market_value, data_type, data_json, 'DONE')
                self.update_state(state='SUCCESS', meta={'status': 'Data scraped and stored successfully'})
                return 'DONE'
        
        strategy.store_fallback_data(ticker_value, market_value, data_type)
        self.update_state(state='FAILURE', meta={'status': 'Scraping partially failed'})
        return 'PARTIAL'
        
    except Exception as e:
        logger.error(f"Error scraping dividends: {e}")
        strategy.store_fallback_data(ticker_value, market_value, data_type)
        self.update_state(state='FAILURE', meta={'status': f'Scraping failed: {str(e)}'})
        return 'ERROR'
    finally:
        if driver:
            driver.quit()



@shared_task(bind=True)
def all_scraper_firestore(self, ticker_value: str, market_value: str):
    """
    Scrape all data types with Firestore check-first approach
    """
    
    try:
        all_data_types = [
            DataType.INCOME_STATEMENT,
            DataType.BALANCE_SHEET,
            DataType.CASH_FLOW,
            DataType.DIVIDENDS,
            DataType.KEY_METRICS_CASH_FLOW,
            DataType.KEY_METRICS_GROWTH,
            DataType.KEY_METRICS_FINANCIAL_HEALTH
        ]
        
        results = {}
        
        # Check existing data first
        strategy = OptimizedScrapingStrategy()
        for data_type in all_data_types:
            existing = strategy.check_existing_data_first(ticker_value, market_value, data_type)
            if existing:
                results[data_type.value] = 'EXISTING'
                logger.info(f"Found existing {data_type.value} for {ticker_value} {market_value}")
            else:
                # This would trigger individual scrapers
                results[data_type.value] = 'PENDING'
        
        self.update_state(state='SUCCESS', meta=results)
        return results
        
    except Exception as e:
        logger.error(f"Error in all_scraper_firestore: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        return {'error': str(e)}

# Helper functions for key metrics scraping
def _click_key_metrics_tab(scraper, data_type: DataType) -> bool:
    """Click the appropriate key metrics tab"""
    tab_map = {
        DataType.KEY_METRICS_CASH_FLOW: "Cash Flow",
        DataType.KEY_METRICS_GROWTH: "Growth",
        DataType.KEY_METRICS_FINANCIAL_HEALTH: "Financial Health"
    }
    
    tab_text = tab_map.get(data_type)
    if not tab_text:
        return False
    
    tab_selectors = [f"//button[contains(., '{tab_text}')]"]
    return scraper.safe_click(tab_selectors) 