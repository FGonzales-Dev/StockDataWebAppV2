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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapingConfig:
    """Configuration for scraping operations"""
    show_browser: bool = False
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
        options = uc.ChromeOptions()
        options.add_argument(f"--window-size={self.config.browser_width},{self.config.browser_height}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "download.default_directory": BASE_DIR + self.config.download_directory,
        }
        options.add_experimental_option("prefs", prefs)
        
        if not self.config.show_browser:
            options.add_argument("--headless")
        
        # Not specifying a binary location, letting undetected-chromedriver search for Chrome
        logger.info("Attempting to initialize Chrome driver without specifying binary location")
        
        try:
            driver = uc.Chrome(options=options)
            logger.info("Successfully initialized Chrome driver")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise
    
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

def scrape_financial_statement_firestore(ticker: str, market: str, data_type: DataType) -> str:
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
        strategy.driver = driver
        
        url = f"https://www.morningstar.com/stocks/{market}/{ticker}/financials"
        driver.get(url)
        logger.info(f"Navigating to {url}")
        
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
            sleep(10)
            
            # Process file
            filename_map = {
                DataType.INCOME_STATEMENT: "Income Statement_Annual_As Originally Reported.xls",
                DataType.BALANCE_SHEET: "Balance Sheet_Annual_As Originally Reported.xls",
                DataType.CASH_FLOW: "Cash Flow_Annual_As Originally Reported.xls"
            }
            
            file_path = BASE_DIR + strategy.config.download_directory + "/" + filename_map[data_type]
            
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                data_json = df.to_json()
                strategy.store_data(ticker, market, data_type, data_json, 'DONE')
                os.remove(file_path)
                return 'DONE'
        
        strategy.store_fallback_data(ticker, market, data_type)
        return 'PARTIAL'
        
    except Exception as e:
        logger.error(f"Error: {e}")
        strategy.store_fallback_data(ticker, market, data_type)
        return 'ERROR'
    finally:
        if driver:
            driver.quit()

@shared_task(bind=True)
def scraper_firestore(self, ticker_value: str, market_value: str, download_type: str):
    """
    Main scraper task with Firestore check-first approach
    """
    try:
        data_type = DataType(download_type)
        
        if data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
            result = scrape_financial_statement_firestore(ticker_value, market_value, data_type)
            
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
def scraper_key_metrics_firestore(self, ticker_value: str, market_value: str, download_type: str):
    """Key metrics scraper with Firestore check-first approach"""
    
    strategy = OptimizedScrapingStrategy()
    progress_recorder = ProgressRecorder(self)
    
    try:
        data_type = DataType(download_type)
        
        # STEP 1: Check if data already exists
        existing_data = strategy.check_existing_data_first(ticker_value, market_value, data_type)
        if existing_data:
            logger.info(f"Found existing {data_type.value} data for {ticker_value} {market_value} - skipping scrape")
            return 'EXISTING'
        
        progress_recorder.set_progress(25, 100, description=f"Scraping {data_type.value}")
        
        driver = strategy.create_driver()
        strategy.driver = driver
        
        url = f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/key-metrics"
        driver.get(url)
        sleep(5)
        
        # Click appropriate tab
        if not _click_key_metrics_tab(strategy, data_type):
            logger.warning(f"Failed to click tab for {data_type.value}")
        
        sleep(3)
        
        # Click Export Data button
        export_selectors = [
            "//button[@id='salEqsvFinancialsPopoverExport']",  # Primary selector based on actual HTML
            "//button[@aria-label='Export']",  # Based on the aria-label attribute
            "//div[@class='sal-financials__exportSection']//button",  # Find button within export section
            "//button[contains(@class, 'mds-button--icon-only__sal')]",  # Based on specific class
            "//button[contains(., 'Export Data')]",  # Original fallback
            "//button[contains(@class, 'export')]"  # General export class fallback
        ]
        
        if not strategy.safe_click(export_selectors):
            logger.warning(f"Failed to click Export Data button for {data_type.value}")
            strategy.store_fallback_data(ticker_value, market_value, data_type)
            return 'ERROR'
        
        sleep(10)  # Wait for download to complete
        progress_recorder.set_progress(75, 100, description="Processing data")
        
        # Export and process
        result = _process_key_metrics_file(strategy, data_type, ticker_value, market_value)
        
        progress_recorder.set_progress(100, 100, description="Completed")
        return result
        
    except Exception as e:
        logger.error(f"Error in key metrics scraping: {e}")
        strategy.store_fallback_data(ticker_value, market_value, data_type)
        return 'ERROR'
    finally:
        if strategy.driver:
            strategy.driver.quit()

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

def _process_key_metrics_file(scraper, data_type: DataType, ticker: str, market: str) -> str:
    """Process downloaded key metrics file"""
    filename_map = {
        DataType.KEY_METRICS_CASH_FLOW: "cashFlow.xls",
        DataType.KEY_METRICS_GROWTH: "growthTable.xls",
        DataType.KEY_METRICS_FINANCIAL_HEALTH: "financialHealth.xls"
    }
    
    file_path = BASE_DIR + scraper.config.download_directory + "/" + filename_map[data_type]
    
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            data_json = df.to_json()
            scraper.store_data(ticker, market, data_type, data_json, 'DONE')
            os.remove(file_path)  # Delete file after successful storage
            return 'DONE'
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            scraper.store_fallback_data(ticker, market, data_type)
            return 'ERROR'
    else:
        logger.warning(f"File not found: {file_path}")
        scraper.store_fallback_data(ticker, market, data_type)
        return 'PARTIAL' 