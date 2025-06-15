"""
Optimized Stock Data Scraper Module
Addresses code duplication, performance issues, and maintainability concerns
"""

import os
import json
import pandas as pd
from time import sleep
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc
from stock_scraper.settings import BASE_DIR
import pyrebase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataType(Enum):
    """Enumeration for different data types to scrape"""
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"
    DIVIDENDS = "DIVIDENDS"
    VALUATION_CASH_FLOW = "VALUATION_CASH_FLOW"
    VALUATION_GROWTH = "VALUATION_GROWTH"
    VALUATION_FINANCIAL_HEALTH = "VALUATION_FINANCIAL_HEALTH"
    VALUATION_OPERATING_EFFICIENCY = "VALUATION_OPERATING_EFFICIENCY"
    OPERATING_PERFORMANCE = "OPERATING_PERFORMANCE"

@dataclass
class ScrapingConfig:
    """Configuration class for scraping parameters"""
    show_browser: bool = False
    element_wait_timeout: int = 30
    page_load_timeout: int = 60
    browser_width: int = 1920
    browser_height: int = 1080
    download_directory: str = "/selenium"
    max_retries: int = 3
    retry_delay: int = 2

@dataclass
class SelectorStrategy:
    """Class to hold multiple selector strategies for robust element finding"""
    strategies: List[Tuple[str, str]]  # (description, xpath)
    
    def __post_init__(self):
        if not self.strategies:
            raise ValueError("At least one selector strategy must be provided")

class OptimizedScraper:
    """Optimized scraper class with improved error handling and code reuse"""
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.driver = None
        self.firebase_config = {
            "apiKey": "AIzaSyD7fxurFiXK0agVyqr1wnfhnymIRCRiPXY",
            "authDomain": "scraper-b0a07.firebaseapp.com",
            "projectId": "scraper-b0a07",
            "storageBucket": "scraper-b0a07.appspot.com",
            "messagingSenderId": "1066439876574",
            "appId": "1:1066439876574:web:d0d4366594823a2d7f874f",
            "measurementId": "G-TJTZ8ZT9CW",
            "databaseURL": "https://scraper-b0a07-default-rtdb.asia-southeast1.firebasedatabase.app"
        }
        self.firebase = pyrebase.initialize_app(self.firebase_config)
        self.database = self.firebase.database()
        
        # Define selector strategies for common elements
        self.selectors = {
            'expand_detail': SelectorStrategy([
                ("Original selector", "//a[contains(., 'Expand Detail View')]"),
                ("Expand link", "//a[contains(text(), 'Expand')]"),
                ("Detail view link", "//a[contains(text(), 'Detail View')]")
            ]),
            'export_button': SelectorStrategy([
                ("Export Data text", "//button[contains(., 'Export Data')]"),
                ("Export by ID", "//button[@id='salEqsvFinancialsPopoverExport']"),
                ("Export by aria-label", "//button[@aria-label='Export']"),
                ("Export by class/icon", "//button[contains(@class, 'mds-button--icon-only__sal') and .//span[@data-mds-icon-name='share']]")
            ]),
            'table_scroller': SelectorStrategy([
                ("Original table scroller", "//div[@class='mds-table__scroller__sal']"),
                ("Generic table scroller", "//div[contains(@class, 'table__scroller')]"),
                ("Table container", "//div[contains(@class, 'table') and contains(@class, 'scroller')]"),
                ("Direct table", "//table")
            ]),
            'time_period_dropdown': SelectorStrategy([
                ("5 Years button", "//button[contains(., '5 Years')]"),
                ("Years button with class", "//button[contains(@class, 'mds-button--secondary') and contains(., 'Years')]"),
                ("Years button with aria-haspopup", "//button[@aria-haspopup='true' and contains(., 'Years')]")
            ]),
            'ten_years_option': SelectorStrategy([
                ("Direct 10 Years match", "//button[contains(., '10 Years')] | //li[contains(., '10 Years')] | //div[contains(., '10 Years')]"),
                ("10 and Years text", "//*[contains(., '10') and contains(., 'Years')]"),
                ("Dropdown 10 option", "//ul//li[contains(text(), '10')] | //div[@role='menu']//div[contains(text(), '10')]")
            ])
        }

    def create_stealth_driver(self) -> uc.Chrome:
        """Create a stealth Chrome driver with optimized configuration"""
        options = uc.ChromeOptions()
        
        # Window and display settings
        options.add_argument(f"--window-size={self.config.browser_width},{self.config.browser_height}")
        
        # Anti-detection measures
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        
        # Download preferences
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Disable images for speed
            "download.default_directory": BASE_DIR + self.config.download_directory,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Headless mode
        if not self.config.show_browser:
            options.add_argument("--headless")
            
        driver = uc.Chrome(options=options)
        
        # Additional stealth measures
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

    def find_element_with_strategies(self, selector_strategy: SelectorStrategy, timeout: int = 10) -> Optional[Any]:
        """Try multiple selector strategies to find an element"""
        for description, xpath in selector_strategy.strategies:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                logger.info(f"Successfully found element using: {description}")
                return element
            except TimeoutException:
                logger.debug(f"Strategy '{description}' failed")
                continue
        
        logger.warning(f"All strategies failed for selector: {selector_strategy}")
        return None

    def safe_click(self, selector_strategy: SelectorStrategy, timeout: int = 10) -> bool:
        """Safely click an element with retry logic"""
        element = self.find_element_with_strategies(selector_strategy, timeout)
        if element:
            try:
                element.click()
                return True
            except Exception as e:
                logger.error(f"Failed to click element: {e}")
        return False

    def retry_operation(self, operation, max_retries: int = None, delay: int = None) -> Any:
        """Retry an operation with exponential backoff"""
        max_retries = max_retries or self.config.max_retries
        delay = delay or self.config.retry_delay
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Operation failed after {max_retries} retries: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                sleep(delay * (2 ** attempt))  # Exponential backoff

    def scrape_financial_data(self, ticker: str, market: str, data_type: DataType) -> str:
        """Scrape financial data from Morningstar"""
        try:
            self.driver = self.create_stealth_driver()
            
            if data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
                return self._scrape_financial_statements(ticker, market, data_type)
            elif data_type == DataType.DIVIDENDS:
                return self._scrape_dividends(ticker, market)
            elif data_type.name.startswith('VALUATION_'):
                return self._scrape_valuation_data(ticker, market, data_type)
            elif data_type == DataType.OPERATING_PERFORMANCE:
                return self._scrape_operating_performance(ticker, market)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Error scraping {data_type.value} for {ticker}: {e}")
            self._store_fallback_data(data_type)
            return 'ERROR'
        finally:
            if self.driver:
                self.driver.quit()

    def _scrape_financial_statements(self, ticker: str, market: str, data_type: DataType) -> str:
        """Scrape income statement, balance sheet, or cash flow data"""
        url = f"https://www.morningstar.com/stocks/{market}/{ticker}/financials"
        self.driver.get(url)
        logger.info(f"Navigated to {url}")
        
        # Click the appropriate tab
        tab_text = data_type.value.replace('_', ' ').title()
        tab_xpath = f"//button[contains(., '{tab_text}')]"
        
        try:
            WebDriverWait(self.driver, self.config.element_wait_timeout).until(
                EC.element_to_be_clickable((By.XPATH, tab_xpath))
            ).click()
            logger.info(f"Successfully clicked {tab_text} button")
            sleep(3)
        except TimeoutException:
            logger.error(f"Failed to find {tab_text} button")
            raise
        
        # Expand detail view
        if self.safe_click(self.selectors['expand_detail']):
            sleep(2)
        
        # Export data
        if self.safe_click(self.selectors['export_button']):
            sleep(10)  # Wait for download
            
            # Read and process the downloaded file
            filename_map = {
                DataType.INCOME_STATEMENT: "Income Statement_Annual_As Originally Reported.xls",
                DataType.BALANCE_SHEET: "Balance Sheet_Annual_As Originally Reported.xls",
                DataType.CASH_FLOW: "Cash Flow_Annual_As Originally Reported.xls"
            }
            
            file_path = BASE_DIR + self.config.download_directory + "/" + filename_map[data_type]
            return self._process_excel_file(file_path, data_type)
        else:
            logger.warning("Failed to export data")
            self._store_fallback_data(data_type)
            return 'PARTIAL'

    def _scrape_dividends(self, ticker: str, market: str) -> str:
        """Scrape dividends data"""
        url = f"https://www.morningstar.com/stocks/{market}/{ticker}/dividends"
        self.driver.get(url)
        logger.info(f"Navigated to {url}")
        
        # Find dividends table
        table_element = self.find_element_with_strategies(self.selectors['table_scroller'], 30)
        if table_element:
            try:
                data = table_element.get_attribute("outerHTML")
                df = pd.read_html(data)
                if df and len(df) > 0:
                    data_json = df[0].to_json()
                    self.database.child("dividends").set({"dividends": data_json})
                    logger.info("Successfully stored dividends data")
                    return 'DONE'
            except Exception as e:
                logger.error(f"Error processing dividends data: {e}")
        
        self._store_fallback_data(DataType.DIVIDENDS)
        return 'PARTIAL'

    def _scrape_valuation_data(self, ticker: str, market: str, data_type: DataType) -> str:
        """Scrape valuation data (cash flow, growth, financial health, operating efficiency)"""
        url = f"https://www.morningstar.com/stocks/{market}/{ticker}/key-metrics"
        self.driver.get(url)
        logger.info(f"Navigated to {url}")
        sleep(3)
        
        # Click appropriate tab
        tab_mapping = {
            DataType.VALUATION_CASH_FLOW: ("keyMetricscashFlow", "cashFlow", "Cash Flow"),
            DataType.VALUATION_GROWTH: ("keyMetricsgrowthTable", "growthTable", "Growth"),
            DataType.VALUATION_FINANCIAL_HEALTH: ("keyMetricsfinancialHealth", "financialHealth", "Financial Health"),
            DataType.VALUATION_OPERATING_EFFICIENCY: ("keyMetricsprofitabilityAndEfficiency", "profitabilityAndEfficiency", "Profitability and Efficiency")
        }
        
        tab_id, data_attr, tab_text = tab_mapping[data_type]
        
        # Try multiple strategies to click the tab
        tab_clicked = False
        strategies = [
            (f"By ID: {tab_id}", f"//button[@id='{tab_id}']"),
            (f"By data attribute: {data_attr}", f"//button[@data='{data_attr}']"),
            (f"By text: {tab_text}", f"//button[contains(., '{tab_text}')]")
        ]
        
        for description, xpath in strategies:
            try:
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
                tab_clicked = True
                logger.info(f"Successfully clicked tab using: {description}")
                break
            except TimeoutException:
                continue
        
        if tab_clicked:
            sleep(3)
            
            # Set time period to 10 years
            self._set_time_period_to_10_years()
            
            # Export data
            if self.safe_click(self.selectors['export_button']):
                sleep(10)
                
                # Process downloaded file
                filename_map = {
                    DataType.VALUATION_CASH_FLOW: "cashFlow.xls",
                    DataType.VALUATION_GROWTH: "growthTable.xls",
                    DataType.VALUATION_FINANCIAL_HEALTH: "financialHealth.xls",
                    DataType.VALUATION_OPERATING_EFFICIENCY: "operatingAndEfficiency.xls"
                }
                
                file_path = BASE_DIR + self.config.download_directory + "/" + filename_map[data_type]
                return self._process_excel_file(file_path, data_type)
        
        self._store_fallback_data(data_type)
        return 'PARTIAL'

    def _scrape_operating_performance(self, ticker: str, market: str) -> str:
        """Scrape operating performance data"""
        url = f"https://www.morningstar.com/stocks/{market}/{ticker}/performance"
        self.driver.get(url)
        logger.info(f"Navigated to {url}")
        
        # Find performance table
        table_element = self.find_element_with_strategies(self.selectors['table_scroller'], 30)
        if table_element:
            try:
                data = table_element.get_attribute("outerHTML")
                df = pd.read_html(data)
                if df and len(df) > 0:
                    data_json = df[0].to_json()
                    self.database.child("operating_performance").set({"operating_performance": data_json})
                    logger.info("Successfully stored operating performance data")
                    return 'DONE'
            except Exception as e:
                logger.error(f"Error processing operating performance data: {e}")
        
        self._store_fallback_data(DataType.OPERATING_PERFORMANCE)
        return 'PARTIAL'

    def _set_time_period_to_10_years(self):
        """Set time period to 10 years for valuation data"""
        if self.safe_click(self.selectors['time_period_dropdown']):
            sleep(2)
            if self.safe_click(self.selectors['ten_years_option']):
                sleep(3)
                logger.info("Successfully set time period to 10 years")
            else:
                logger.warning("Could not select 10 years option")
        else:
            logger.warning("Could not open time period dropdown")

    def _process_excel_file(self, file_path: str, data_type: DataType) -> str:
        """Process downloaded Excel file and store in database"""
        try:
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                data_json = df.to_json()
                
                # Store in appropriate database location
                db_key_map = {
                    DataType.INCOME_STATEMENT: "income_statement",
                    DataType.BALANCE_SHEET: "balance_sheet",
                    DataType.CASH_FLOW: "cash_flow",
                    DataType.VALUATION_CASH_FLOW: "valuation_cash_flow",
                    DataType.VALUATION_GROWTH: "valuation_growth",
                    DataType.VALUATION_FINANCIAL_HEALTH: "valuation_financial_health",
                    DataType.VALUATION_OPERATING_EFFICIENCY: "valuation_operating_efficiency"
                }
                
                db_key = db_key_map[data_type]
                self.database.child(db_key).set({db_key: data_json})
                logger.info(f"Successfully stored {data_type.value} data")
                
                # Clean up file
                os.remove(file_path)
                return 'DONE'
            else:
                logger.error(f"File not found: {file_path}")
                self._store_fallback_data(data_type)
                return 'PARTIAL'
        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
            self._store_fallback_data(data_type)
            return 'ERROR'

    def _store_fallback_data(self, data_type: DataType):
        """Store fallback data when scraping fails"""
        fallback_data = json.dumps({data_type.value.lower(): {"none": "no data"}})
        
        db_key_map = {
            DataType.INCOME_STATEMENT: "income_statement",
            DataType.BALANCE_SHEET: "balance_sheet", 
            DataType.CASH_FLOW: "cash_flow",
            DataType.DIVIDENDS: "dividends",
            DataType.VALUATION_CASH_FLOW: "valuation_cash_flow",
            DataType.VALUATION_GROWTH: "valuation_growth",
            DataType.VALUATION_FINANCIAL_HEALTH: "valuation_financial_health",
            DataType.VALUATION_OPERATING_EFFICIENCY: "valuation_operating_efficiency",
            DataType.OPERATING_PERFORMANCE: "operating_performance"
        }
        
        db_key = db_key_map[data_type]
        self.database.child(db_key).set({db_key: fallback_data})
        logger.info(f"Stored fallback data for {data_type.value}")

    def scrape_all_data(self, ticker: str, market: str) -> Dict[str, str]:
        """Scrape all available data types for a ticker"""
        results = {}
        data_types = list(DataType)
        
        for data_type in data_types:
            try:
                logger.info(f"Starting {data_type.value} scraping for {ticker}")
                result = self.scrape_financial_data(ticker, market, data_type)
                results[data_type.value] = result
                sleep(2)  # Brief pause between scrapes
            except Exception as e:
                logger.error(f"Failed to scrape {data_type.value}: {e}")
                results[data_type.value] = 'ERROR'
        
        return results

    def cleanup_download_directory(self):
        """Clean up the download directory"""
        download_dir = BASE_DIR + self.config.download_directory
        if os.path.exists(download_dir):
            for filename in os.listdir(download_dir):
                file_path = os.path.join(download_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

# Utility functions for backward compatibility
def create_optimized_scraper(show_browser: bool = False) -> OptimizedScraper:
    """Create an optimized scraper instance"""
    config = ScrapingConfig(show_browser=show_browser)
    return OptimizedScraper(config)

def scrape_data_optimized(ticker: str, market: str, data_type: str, show_browser: bool = False) -> str:
    """Optimized scraping function for single data type"""
    scraper = create_optimized_scraper(show_browser)
    scraper.cleanup_download_directory()
    
    try:
        dt = DataType(data_type)
        return scraper.scrape_financial_data(ticker, market, dt)
    except ValueError:
        logger.error(f"Invalid data type: {data_type}")
        return 'ERROR'
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return 'ERROR' 