"""
Flexible Scraping Manager
Works with or without Redis/Celery
"""

import logging
from typing import Dict, Optional, Tuple, Any
from .firestore_storage import DataType, get_storage
from .tasks_firestore import scrape_financial_statement_firestore

logger = logging.getLogger(__name__)


class ScrapingManager:
    """
    Smart scraping manager that can work with or without Redis/Celery
    """
    
    def __init__(self):
        # Check configuration (environment variable takes priority)
        import os
        self.scraping_mode = os.getenv('SCRAPING_MODE')
        
        if not self.scraping_mode:
            try:
                import scraping_mode_config
                self.scraping_mode = getattr(scraping_mode_config, 'SCRAPING_MODE', 'auto')
                self.redis_fallback = getattr(scraping_mode_config, 'REDIS_FALLBACK_TO_DIRECT', True)
            except ImportError:
                self.scraping_mode = 'auto'
                self.redis_fallback = True
        else:
            self.redis_fallback = True  # Default for env var mode
        
        # Check system availability
        self.redis_available = self._check_redis_available()
        self.celery_available = self._check_celery_available()
        
        # Determine actual mode to use
        if self.scraping_mode == 'direct':
            self.use_background_tasks = False
        elif self.scraping_mode == 'background':
            self.use_background_tasks = self.redis_available and self.celery_available
        else:  # auto mode
            self.use_background_tasks = self.redis_available and self.celery_available
        
        logger.info(f"ScrapingManager initialized - Mode: {self.scraping_mode}, Redis: {self.redis_available}, Celery: {self.celery_available}, Using background: {self.use_background_tasks}")
    
    def _check_redis_available(self) -> bool:
        """Check if Redis is available"""
        try:
            import redis
            from django.conf import settings
            redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379')
            r = redis.from_url(redis_url)
            r.ping()
            return True
        except Exception as e:
            logger.info(f"Redis not available: {e}")
            return False
    
    def _check_celery_available(self) -> bool:
        """Check if Celery is available"""
        try:
            from celery import current_app
            return current_app is not None
        except Exception as e:
            logger.info(f"Celery not available: {e}")
            return False
    
    def scrape_stock_data(self, ticker: str, market: str, data_type: str) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """
        Scrape stock data with automatic background/direct detection
        
        Returns:
            Tuple[mode, task_id, context_data]
            - mode: 'background' or 'direct'
            - task_id: Task ID if background, None if direct
            - context_data: Data for template rendering
        """
        
        # First check if data already exists
        try:
            data_type_enum = DataType(data_type)
            storage = get_storage()
            existing_data = storage.check_data_exists(ticker, market, data_type_enum)
            
            if existing_data and existing_data['status'] == 'DONE':
                logger.info(f"Found existing data for {ticker} {market} {data_type}")
                return 'existing', 'existing_data', {
                    'data_exists': True,
                    'message': f"Data for {ticker} ({market}) - {data_type} already exists and is ready for download!",
                    'scraped_at': existing_data['scraped_at'].strftime("%Y-%m-%d %H:%M:%S") if existing_data['scraped_at'] else "Unknown"
                }
        except ValueError:
            return 'error', None, {'error': f'Invalid data type: {data_type}'}
        
        # Data doesn't exist, need to scrape
        if self.use_background_tasks:
            return self._scrape_background(ticker, market, data_type)
        else:
            return self._scrape_direct(ticker, market, data_type)
    
    def _scrape_background(self, ticker: str, market: str, data_type: str) -> Tuple[str, str, Dict[str, Any]]:
        """Scrape using Celery background tasks"""
        try:
            logger.info(f"Starting background scraping for {ticker} {market} {data_type}")
            
            if data_type in ["INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW"]:
                from .tasks_firestore import scraper_firestore
                task = scraper_firestore.delay(ticker, market, data_type)
            elif data_type in ["KEY_METRICS_CASH_FLOW", "KEY_METRICS_GROWTH", "KEY_METRICS_FINANCIAL_HEALTH"]:
                from .tasks_firestore import scraper_key_metrics_firestore
                task = scraper_key_metrics_firestore.delay(ticker, market, data_type)
            elif data_type == "DIVIDENDS":
                from .tasks_firestore import scraper_dividends_firestore
                task = scraper_dividends_firestore.delay(ticker, market)
            elif data_type == "ALL":
                from .tasks_firestore import all_scraper_firestore
                task = all_scraper_firestore.delay(ticker, market)
            else:
                return 'error', None, {'error': f'Unsupported data type: {data_type}'}
            
            return 'background', task.id, {
                'task_id': task.id,
                'message': 'Background scraping started. Please wait...'
            }
            
        except Exception as e:
            logger.error(f"Background scraping failed, falling back to direct: {e}")
            return self._scrape_direct(ticker, market, data_type)
    
    def _scrape_direct(self, ticker: str, market: str, data_type: str) -> Tuple[str, None, Dict[str, Any]]:
        """Scrape directly (synchronously)"""
        logger.info(f"Starting direct scraping for {ticker} {market} {data_type}")
        
        try:
            if data_type in ["INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW"]:
                result = scrape_financial_statement_firestore(ticker, market, DataType(data_type))
            elif data_type in ["KEY_METRICS_CASH_FLOW", "KEY_METRICS_GROWTH", "KEY_METRICS_FINANCIAL_HEALTH"]:
                result = self._scrape_key_metrics_direct(ticker, market, DataType(data_type))
            elif data_type == "DIVIDENDS":
                result = self._scrape_dividends_direct(ticker, market)
            elif data_type == "ALL":
                result = self._scrape_all_direct(ticker, market)
            else:
                return 'error', None, {'error': f'Unsupported data type: {data_type}'}
            
            # Generate message based on result
            if result == 'EXISTING':
                message = f"Data for {ticker} ({market}) - {data_type} already existed in storage"
            elif result == 'DONE':
                message = f"Successfully scraped and stored {data_type} data for {ticker} ({market})"
            elif result == 'PARTIAL':
                message = f"Partially scraped {data_type} data for {ticker} ({market})"
            elif result == 'ERROR':
                message = f"Failed to scrape {data_type} data for {ticker} ({market})"
            else:
                message = f"Scraping completed with status: {result}"
            
            return 'direct', None, {
                'result': result,
                'message': message,
                'scraping_complete': True
            }
            
        except Exception as e:
            logger.error(f"Direct scraping failed: {e}")
            return 'error', None, {'error': f'Scraping failed: {str(e)}'}
    
    def _scrape_key_metrics_direct(self, ticker: str, market: str, data_type: DataType) -> str:
        """Direct key metrics scraping"""
        from .views_firestore import scrape_key_metrics_direct
        return scrape_key_metrics_direct(ticker, market, data_type)
    
    def _scrape_dividends_direct(self, ticker: str, market: str) -> str:
        """Direct dividends scraping"""
        from .views_firestore import scrape_dividends_direct
        return scrape_dividends_direct(ticker, market)
    
    def _scrape_all_direct(self, ticker: str, market: str) -> str:
        """Direct all data scraping"""
        from .views_firestore import scrape_all_direct
        return scrape_all_direct(ticker, market)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status (works for both background and direct)"""
        if task_id in ['existing_data', 'direct_execution']:
            return {
                'state': 'SUCCESS',
                'result': 'DONE',
                'firestore': True,
                'message': 'Data ready for download',
                'progress': 100
            }
        
        if not self.use_background_tasks:
            return {
                'state': 'SUCCESS',
                'result': 'DONE',
                'firestore': True,
                'message': 'Direct execution completed',
                'progress': 100
            }
        
        try:
            from celery.result import AsyncResult
            task = AsyncResult(task_id)
            
            data = {
                'state': task.state,
                'result': task.result,
                'firestore': True
            }
            
            # Add progress info based on state
            if task.state == 'PROGRESS':
                if isinstance(task.result, dict):
                    data.update(task.result)
                else:
                    data['progress'] = 50
                    data['message'] = 'Scraping in progress...'
            elif task.state == 'SUCCESS':
                data['progress'] = 100
                data['message'] = 'Scraping completed successfully'
            elif task.state == 'FAILURE':
                data['error'] = str(task.result)
                data['message'] = f'Task failed: {str(task.result)}'
            elif task.state == 'PENDING':
                data['progress'] = 0
                data['message'] = 'Task is waiting to be processed'
            
            return data
            
        except Exception as e:
            logger.warning(f"Failed to get task status: {e}")
            return {
                'state': 'SUCCESS',
                'result': 'DONE',
                'firestore': True,
                'message': 'Task completed',
                'progress': 100
            }


# Global instance
scraping_manager = ScrapingManager()


def get_scraping_manager() -> ScrapingManager:
    """Get the global scraping manager instance"""
    return scraping_manager 