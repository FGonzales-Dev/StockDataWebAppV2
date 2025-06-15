"""
Optimized Celery Tasks for Stock Data Scraping
Refactored for better performance, error handling, and code reuse
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
import pyrebase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase configuration
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
database = firebase.database()

@dataclass
class ScrapingConfig:
    """Configuration for scraping operations"""
    show_browser: bool = False
    element_wait_timeout: int = 30
    download_directory: str = "/selenium"
    browser_width: int = 1920
    browser_height: int = 1080
    max_retries: int = 3

class DataType(Enum):
    """Data types that can be scraped"""
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"
    DIVIDENDS = "DIVIDENDS"
    VALUATION_CASH_FLOW = "VALUATION_CASH_FLOW"
    VALUATION_GROWTH = "VALUATION_GROWTH"
    VALUATION_FINANCIAL_HEALTH = "VALUATION_FINANCIAL_HEALTH"
    VALUATION_OPERATING_EFFICIENCY = "VALUATION_OPERATING_EFFICIENCY"
    OPERATING_PERFORMANCE = "OPERATING_PERFORMANCE"

class OptimizedScrapingStrategy:
    """Optimized base scraping strategy with common functionality"""
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.driver = None
    
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
        
        return uc.Chrome(options=options)
    
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
    
    def store_data(self, data_type: DataType, data: str):
        """Store data in Firebase"""
        db_key = data_type.value.lower()
        database.child(db_key).set({db_key: data})
        logger.info(f"Stored {data_type.value} data")
    
    def store_fallback_data(self, data_type: DataType):
        """Store fallback data when scraping fails"""
        fallback = json.dumps({data_type.value.lower(): {"none": "no data"}})
        self.store_data(data_type, fallback)

def scrape_financial_statement_optimized(ticker: str, market: str, data_type: DataType) -> str:
    """Optimized financial statement scraper"""
    strategy = OptimizedScrapingStrategy()
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
        
        # Expand and export
        expand_selectors = [
            "//a[contains(., 'Expand Detail View')]",
            "//a[contains(text(), 'Expand')]"
        ]
        strategy.safe_click(expand_selectors)
        sleep(2)
        
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
                strategy.store_data(data_type, data_json)
                os.remove(file_path)
                return 'DONE'
        
        strategy.store_fallback_data(data_type)
        return 'PARTIAL'
        
    except Exception as e:
        logger.error(f"Error: {e}")
        strategy.store_fallback_data(data_type)
        return 'ERROR'
    finally:
        if driver:
            driver.quit()

@shared_task(bind=True)
def scraper_optimized(self, ticker_value: str, market_value: str, download_type: str):
    """Optimized main scraper task"""
    try:
        data_type = DataType(download_type)
        
        if data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
            return scrape_financial_statement_optimized(ticker_value, market_value, data_type)
        else:
            logger.error(f"Data type {download_type} not yet optimized")
            return 'ERROR'
            
    except ValueError:
        logger.error(f"Invalid data type: {download_type}")
        return 'ERROR'
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return 'ERROR'

@shared_task(bind=True)
def scraper_dividends_optimized(self, ticker_value: str, market_value: str):
    """Optimized dividends scraper task"""
    scraper = OptimizedScrapingStrategy()
    driver = None
    
    try:
        driver = scraper.create_driver()
        scraper.driver = driver
        
        url = f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/dividends"
        driver.get(url)
        logger.info(f"Navigating to {url}")
        
        table_selectors = [
            "//div[@class='mds-table__scroller__sal']",
            "//div[contains(@class, 'table__scroller')]",
            "//div[contains(@class, 'table') and contains(@class, 'scroller')]",
            "//table"
        ]
        
        table_element = scraper.find_element_safely(table_selectors, 30)
        if table_element:
            data = table_element.get_attribute("outerHTML")
            df = pd.read_html(data)
            if df and len(df) > 0:
                data_json = df[0].to_json()
                scraper.store_data(DataType.DIVIDENDS, data_json)
                return 'DONE'
        
        scraper.store_fallback_data(DataType.DIVIDENDS)
        return 'PARTIAL'
        
    except Exception as e:
        logger.error(f"Error scraping dividends: {e}")
        scraper.store_fallback_data(DataType.DIVIDENDS)
        return 'ERROR'
    finally:
        if driver:
            driver.quit()

@shared_task(bind=True) 
def scraper_valuation_optimized(self, ticker_value: str, market_value: str, download_type: str):
    """Optimized valuation scraper task"""
    try:
        data_type = DataType(download_type)
        scraper = OptimizedScrapingStrategy()
        driver = None
        
        try:
            driver = scraper.create_driver()
            scraper.driver = driver
            
            url = f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/key-metrics"
            driver.get(url)
            logger.info(f"Navigating to {url}")
            sleep(3)
            
            # Click appropriate tab
            if not _click_valuation_tab(scraper, data_type):
                logger.warning(f"Failed to click tab for {data_type.value}")
            
            sleep(3)
            
            # Set time period to 10 years
            _set_time_period(scraper)
            
            # Export data
            export_selectors = [
                "//button[@id='salKeyStatsPopoverExport']",
                "//button[@aria-label='Export']",
                "//button[contains(@class, 'mds-button--icon-only__sal') and .//span[@data-mds-icon-name='share']]"
            ]
            
            if scraper.safe_click(export_selectors):
                sleep(10)
                return _process_valuation_file(scraper, data_type)
            else:
                scraper.store_fallback_data(data_type)
                return 'PARTIAL'
                
        except Exception as e:
            logger.error(f"Error scraping {data_type.value}: {e}")
            scraper.store_fallback_data(data_type)
            return 'ERROR'
        finally:
            if driver:
                driver.quit()
    except ValueError:
        logger.error(f"Invalid valuation data type: {download_type}")
        return 'ERROR'

@shared_task(bind=True)
def scraper_operating_performance_optimized(self, ticker_value: str, market_value: str):
    """Optimized operating performance scraper task"""
    scraper = OptimizedScrapingStrategy()
    driver = None
    
    try:
        driver = scraper.create_driver()
        scraper.driver = driver
        
        url = f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/performance"
        driver.get(url)
        logger.info(f"Navigating to {url}")
        
        table_selectors = [
            "//div[@class='mds-table__scroller__sal']",
            "//div[contains(@class, 'table__scroller')]",
            "//table"
        ]
        
        table_element = scraper.find_element_safely(table_selectors, 30)
        if table_element:
            data = table_element.get_attribute("outerHTML")
            df = pd.read_html(data)
            if df and len(df) > 0:
                data_json = df[0].to_json()
                scraper.store_data(DataType.OPERATING_PERFORMANCE, data_json)
                return 'DONE'
        
        scraper.store_fallback_data(DataType.OPERATING_PERFORMANCE)
        return 'PARTIAL'
        
    except Exception as e:
        logger.error(f"Error scraping operating performance: {e}")
        scraper.store_fallback_data(DataType.OPERATING_PERFORMANCE)
        return 'ERROR'
    finally:
        if driver:
            driver.quit()

@shared_task(bind=True)
def all_scraper_optimized(self, ticker_value: str, market_value: str):
    """Optimized all-in-one scraper task"""
    results = {}
    data_types = [
        DataType.INCOME_STATEMENT,
        DataType.BALANCE_SHEET,
        DataType.CASH_FLOW,
        DataType.DIVIDENDS,
        DataType.VALUATION_CASH_FLOW,
        DataType.VALUATION_GROWTH,
        DataType.VALUATION_FINANCIAL_HEALTH,
        DataType.VALUATION_OPERATING_EFFICIENCY,
        DataType.OPERATING_PERFORMANCE
    ]
    
    for data_type in data_types:
        try:
            logger.info(f"Scraping {data_type.value} for {ticker_value}")
            
            if data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
                result = scrape_financial_statement_optimized(ticker_value, market_value, data_type)
            elif data_type == DataType.DIVIDENDS:
                result = scraper_dividends_optimized(ticker_value, market_value)
            elif data_type.name.startswith('VALUATION_'):
                result = scraper_valuation_optimized(ticker_value, market_value, data_type.value)
            elif data_type == DataType.OPERATING_PERFORMANCE:
                result = scraper_operating_performance_optimized(ticker_value, market_value)
            
            results[data_type.value] = result
            sleep(2)  # Brief pause between scrapes
            
        except Exception as e:
            logger.error(f"Failed to scrape {data_type.value}: {e}")
            results[data_type.value] = 'ERROR'
    
    return results 

def _click_valuation_tab(scraper, data_type: DataType) -> bool:
    """Click the appropriate valuation tab"""
    tab_mapping = {
        DataType.VALUATION_CASH_FLOW: ("keyMetricscashFlow", "Cash Flow"),
        DataType.VALUATION_GROWTH: ("keyMetricsgrowthTable", "Growth"),
        DataType.VALUATION_FINANCIAL_HEALTH: ("keyMetricsfinancialHealth", "Financial Health"),
        DataType.VALUATION_OPERATING_EFFICIENCY: ("keyMetricsprofitabilityAndEfficiency", "Profitability")
    }
    
    tab_id, tab_text = tab_mapping[data_type]
    selectors = [
        f"//button[@id='{tab_id}']",
        f"//button[contains(., '{tab_text}')]"
    ]
    
    return scraper.safe_click(selectors)

def _set_time_period(scraper):
    """Set time period to 10 years"""
    # Click dropdown
    dropdown_selectors = [
        "//button[contains(., '5 Years')]",
        "//button[contains(@class, 'mds-button--secondary') and contains(., 'Years')]"
    ]
    
    if scraper.safe_click(dropdown_selectors):
        sleep(2)
        # Select 10 years
        ten_years_selectors = [
            "//button[contains(., '10 Years')]",
            "//li[contains(., '10 Years')]",
            "//*[contains(., '10') and contains(., 'Years')]"
        ]
        scraper.safe_click(ten_years_selectors)
        sleep(3)

def _process_valuation_file(scraper, data_type: DataType) -> str:
    """Process downloaded valuation file"""
    filename_map = {
        DataType.VALUATION_CASH_FLOW: "cashFlow.xls",
        DataType.VALUATION_GROWTH: "growthTable.xls",
        DataType.VALUATION_FINANCIAL_HEALTH: "financialHealth.xls",
        DataType.VALUATION_OPERATING_EFFICIENCY: "operatingAndEfficiency.xls"
    }
    
    file_path = BASE_DIR + scraper.config.download_directory + "/" + filename_map[data_type]
    
    try:
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            data_json = df.to_json()
            scraper.store_data(data_type, data_json)
            os.remove(file_path)
            return 'DONE'
        else:
            scraper.store_fallback_data(data_type)
            return 'PARTIAL'
    except Exception as e:
        logger.error(f"Error processing valuation file: {e}")
        scraper.store_fallback_data(data_type)
        return 'ERROR' 