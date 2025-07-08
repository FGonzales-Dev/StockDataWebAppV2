"""
Firestore Storage System for Stock Data
Replaces Firebase Realtime Database with Firestore for better querying and structure
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import firebase_admin
from firebase_admin import credentials, firestore
from enum import Enum

logger = logging.getLogger(__name__)

class DataType(Enum):
    """Data types that can be scraped"""
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"
    DIVIDENDS = "DIVIDENDS"
    KEY_METRICS_CASH_FLOW = "KEY_METRICS_CASH_FLOW"
    KEY_METRICS_GROWTH = "KEY_METRICS_GROWTH"
    KEY_METRICS_FINANCIAL_HEALTH = "KEY_METRICS_FINANCIAL_HEALTH"
    KEY_METRICS_PROFITABILITYANDEFFICIENCY = "KEY_METRICS_PROFITABILITYANDEFFICIENCY"
    KEY_METRICS_FINANCIAL_SUMMARY = "KEY_METRICS_FINANCIAL_SUMMARY"
    

@dataclass
class StockDataRecord:
    """Structure for stock data records"""
    ticker: str
    market: str
    data_type: str
    data: str
    scraped_at: datetime
    status: str  # 'DONE', 'PARTIAL', 'ERROR'

class FirestoreStorage:
    """Firestore-based storage for stock data"""
    
    def __init__(self):
        # Initialize Firestore with service account JSON file
        if not firebase_admin._apps:
            # Try to get service account path from environment variable first
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'config/scraper-b0a07-firebase-adminsdk-qtqbw-b80c90626b.json')
            
            try:
                # Use service account JSON file
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logger.info(f"Firebase initialized with service account: {service_account_path}")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase with service account: {e}")
                logger.info("Make sure your firebase-service-account.json file is in the config/ directory")
                raise
        
        self.db = firestore.client()
        self.collection_name = "stock_data"

    def check_data_exists(self, ticker: str, market: str, data_type: DataType) -> Optional[Dict]:
        """
        Check if data already exists for ticker + market + data_type combination
        Returns the data if found, None if not found
        """
        try:
            # Query for specific ticker + market + data_type combination
            docs = self.db.collection(self.collection_name)\
                .where('ticker', '==', ticker.upper())\
                .where('market', '==', market.upper())\
                .where('data_type', '==', data_type.value)\
                .limit(1)\
                .get()
            
            if docs:
                doc_data = docs[0].to_dict()
                logger.info(f"Found existing data for {ticker} {market} {data_type.value}")
                return {
                    'data': doc_data['data'],
                    'scraped_at': doc_data['scraped_at'],
                    'status': doc_data['status']
                }
            
            logger.info(f"No existing data found for {ticker} {market} {data_type.value}")
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing data: {e}")
            return None

    def store_data(self, ticker: str, market: str, data_type: DataType, data: str, status: str = 'DONE') -> bool:
        """
        Store scraped data in Firestore
        Returns True if successful
        """
        try:
            # Create document ID from ticker + market + data_type for easy updates
            doc_id = f"{ticker.upper()}_{market.upper()}_{data_type.value}"
            
            stock_record = {
                'ticker': ticker.upper(),
                'market': market.upper(),
                'data_type': data_type.value,
                'data': data,
                'scraped_at': datetime.utcnow(),
                'status': status
            }
            
            # Store in Firestore
            self.db.collection(self.collection_name).document(doc_id).set(stock_record)
            
            logger.info(f"Stored data for {ticker} {market} {data_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            return False

    def get_all_data_for_stock(self, ticker: str, market: str) -> Dict[str, Dict]:
        """
        Get all data types for a specific ticker + market combination
        Returns dict with data_type as key and data as value
        """
        try:
            docs = self.db.collection(self.collection_name)\
                .where('ticker', '==', ticker.upper())\
                .where('market', '==', market.upper())\
                .get()
            
            stock_data = {}
            for doc in docs:
                doc_data = doc.to_dict()
                data_type = doc_data['data_type']
                stock_data[data_type] = {
                    'data': doc_data['data'],
                    'scraped_at': doc_data['scraped_at'],
                    'status': doc_data['status']
                }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error retrieving all data for stock: {e}")
            return {}

    def get_data_by_type(self, data_type: DataType) -> List[Dict]:
        """
        Get all records of a specific data type
        """
        try:
            docs = self.db.collection(self.collection_name)\
                .where('data_type', '==', data_type.value)\
                .get()
            
            results = []
            for doc in docs:
                results.append(doc.to_dict())
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving data by type: {e}")
            return []

    def update_data(self, ticker: str, market: str, data_type: DataType, data: str, status: str = 'DONE') -> bool:
        """
        Update existing data (same as store_data since we use set() which overwrites)
        """
        return self.store_data(ticker, market, data_type, data, status)

    def delete_data(self, ticker: str, market: str, data_type: DataType = None) -> bool:
        """
        Delete data for ticker + market combination
        If data_type is specified, delete only that type, otherwise delete all
        """
        try:
            query = self.db.collection(self.collection_name)\
                .where('ticker', '==', ticker.upper())\
                .where('market', '==', market.upper())
            
            if data_type:
                query = query.where('data_type', '==', data_type.value)
            
            docs = query.get()
            
            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} records for {ticker} {market}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting data: {e}")
            return False

    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            docs = self.db.collection(self.collection_name).get()
            
            stats = {
                'total_records': len(docs),
                'by_data_type': {},
                'by_ticker': {},
                'by_status': {}
            }
            
            for doc in docs:
                data = doc.to_dict()
                data_type = data['data_type']
                ticker = data['ticker']
                status = data['status']
                
                # Count by data type
                stats['by_data_type'][data_type] = stats['by_data_type'].get(data_type, 0) + 1
                
                # Count by ticker
                stats['by_ticker'][ticker] = stats['by_ticker'].get(ticker, 0) + 1
                
                # Count by status
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

    def save_email_subscription(self, email: str) -> bool:
        """
        Save email subscription to Firestore
        Returns True if successful
        """
        try:
            # Use email as document ID to prevent duplicates
            doc_id = email.replace('@', '_at_').replace('.', '_dot_')
            
            subscription_record = {
                'email': email,
                'subscribed_at': datetime.utcnow(),
                'status': 'active'
            }
            
            # Store in a separate collection for email subscriptions
            self.db.collection('email_subscriptions').document(doc_id).set(subscription_record)
            
            logger.info(f"Saved email subscription for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving email subscription: {e}")
            return False

    def check_email_subscription(self, email: str) -> bool:
        """
        Check if email is already subscribed
        Returns True if subscribed, False if not
        """
        try:
            doc_id = email.replace('@', '_at_').replace('.', '_dot_')
            doc = self.db.collection('email_subscriptions').document(doc_id).get()
            
            if doc.exists:
                logger.info(f"Email {email} is already subscribed")
                return True
            else:
                logger.info(f"Email {email} is not subscribed")
                return False
                
        except Exception as e:
            logger.error(f"Error checking email subscription: {e}")
            return False

# Global storage instance
storage_instance = None

def get_storage() -> FirestoreStorage:
    """Get global storage instance"""
    global storage_instance
    if storage_instance is None:
        storage_instance = FirestoreStorage()
    return storage_instance

def check_existing_data(ticker: str, market: str, data_type: DataType) -> Optional[str]:
    """
    Convenience function to check if data exists before scraping
    Returns existing data if available, None if needs to be scraped
    """
    storage = get_storage()
    existing_data = storage.check_data_exists(ticker, market, data_type)
    if existing_data and existing_data['status'] == 'DONE':
        return existing_data['data']
    return None

def store_scraped_data(ticker: str, market: str, data_type: DataType, data: str, status: str = 'DONE') -> bool:
    """
    Convenience function to store scraped data
    """
    storage = get_storage()
    return storage.store_data(ticker, market, data_type, data, status) 