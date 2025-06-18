"""
Firestore-based Views for Stock Data Scraping
Check Firestore first, scrape only if data doesn't exist
"""

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
from .tasks_firestore import (
    scrape_financial_statement_firestore,
)
from .firestore_storage import (
    FirestoreStorage,
    DataType,
    get_storage,
    check_existing_data
)
from celery.result import AsyncResult
import logging

logger = logging.getLogger(__name__)

def scrape_dividends_direct(ticker: str, market: str) -> str:
    """Direct dividends scraping without task queue"""
    try:
        from .tasks_firestore import OptimizedScrapingStrategy
        
        data_type = DataType.DIVIDENDS
        strategy = OptimizedScrapingStrategy()
        
        # Check existing data first
        existing_data = strategy.check_existing_data_first(ticker, market, data_type)
        if existing_data:
            logger.info(f"Found existing {data_type.value} data for {ticker} {market}")
            return 'EXISTING'
        
        # TODO: Implement actual dividends scraping logic
        # For now, store placeholder data
        placeholder_data = json.dumps({"dividends": [{"note": "Dividends scraping not yet implemented"}]})
        strategy.store_data(ticker, market, data_type, placeholder_data, 'PARTIAL')
        
        return 'PARTIAL'
        
    except Exception as e:
        logger.error(f"Error in dividends scraping: {e}")
        return 'ERROR'

def scrape_key_metrics_direct(ticker: str, market: str, data_type: DataType) -> str:
    """Direct key metrics scraping without task queue"""
    try:
        from .tasks_firestore import OptimizedScrapingStrategy
        
        strategy = OptimizedScrapingStrategy()
        
        # Check existing data first
        existing_data = strategy.check_existing_data_first(ticker, market, data_type)
        if existing_data:
            logger.info(f"Found existing {data_type.value} data for {ticker} {market}")
            return 'EXISTING'
        
        # TODO: Implement actual key metrics scraping logic
        # For now, store placeholder data
        placeholder_data = json.dumps({data_type.value.lower(): [{"note": f"{data_type.value} scraping not yet implemented"}]})
        strategy.store_data(ticker, market, data_type, placeholder_data, 'PARTIAL')
        
        return 'PARTIAL'
        
    except Exception as e:
        logger.error(f"Error in key metrics scraping: {e}")
        return 'ERROR'

def scrape_all_direct(ticker: str, market: str) -> str:
    """Direct scraping of all data types"""
    try:
        results = []
        
        # Scrape all financial statements
        for data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
            result = scrape_financial_statement_firestore(ticker, market, data_type)
            results.append(result)
        
        # Scrape other data types
        results.append(scrape_dividends_direct(ticker, market))
        
        # Scrape key metrics data
        for data_type in [DataType.KEY_METRICS_CASH_FLOW, DataType.KEY_METRICS_GROWTH, 
                         DataType.KEY_METRICS_FINANCIAL_HEALTH]:
            result = scrape_key_metrics_direct(ticker, market, data_type)
            results.append(result)
        
        # Determine overall result
        if all(r in ['DONE', 'EXISTING'] for r in results):
            return 'DONE'
        elif any(r in ['DONE', 'EXISTING', 'PARTIAL'] for r in results):
            return 'PARTIAL'
        else:
            return 'ERROR'
            
    except Exception as e:
        logger.error(f"Error in scrape_all_direct: {e}")
        return 'ERROR'

@csrf_exempt
def scrape_firestore(request):
    """
    Firestore-based scraping endpoint
    Checks Firestore first, scrapes directly if data doesn't exist
    """
    
    if request.method == 'POST':
        ticker_value = request.POST.get("ticker", "").upper()
        market_value = request.POST.get("market", "").upper()
        download_type = request.POST.get("download_type", "")
        
        if not ticker_value or not market_value or not download_type:
            return render(request, "../templates/stockData.html", {
                "error": "Please provide ticker, market, and download type"
            })
        
        if 'get_data' in request.POST:
            # Check if data already exists first
            try:
                data_type = DataType(download_type)
                storage = get_storage()
                existing_data = storage.check_data_exists(ticker_value, market_value, data_type)
                
                if existing_data and existing_data['status'] == 'DONE':
                    # Data already exists, show success screen with download option immediately
                    logger.info(f"Found existing data for {ticker_value} {market_value} {download_type}")
                    return render(request, "../templates/loadScreen.html", {
                        "download_type": download_type,
                        "ticker": ticker_value,
                        "market": market_value,
                        "firestore_mode": True,
                        "data_already_exists": True,  # Flag to show success section immediately
                        "scraped_at": existing_data['scraped_at'].strftime("%Y-%m-%d %H:%M:%S") if existing_data['scraped_at'] else "Unknown",
                        "task_id": "existing_data",  # Dummy task ID for form
                        "message": f"Data for {ticker_value} ({market_value}) - {download_type} already exists and is ready for download!"
                    })
                
            except ValueError:
                return render(request, "../templates/stockData.html", {
                    "error": f"Invalid download type: {download_type}"
                })
            
            # Use the smart scraping manager (auto-detects Redis/Celery availability)
            from .scraping_manager import get_scraping_manager
            
            scraping_manager = get_scraping_manager()
            mode, task_id, context_data = scraping_manager.scrape_stock_data(ticker_value, market_value, download_type)
            
            logger.info(f"Scraping mode: {mode}, Task ID: {task_id}")
            
            # Handle different modes
            if mode == 'error':
                return render(request, "../templates/stockData.html", context_data)
            
            elif mode == 'existing':
                # Data already exists, show loading screen with success
                return render(request, "../templates/loadScreen.html", {
                    "download_type": download_type,
                    "ticker": ticker_value,
                    "market": market_value,
                    "firestore_mode": True,
                    "data_already_exists": True,
                    "task_id": task_id,
                    **context_data
                })
            
            elif mode == 'background':
                # Background task started, show loading screen
                return render(request, "../templates/loadScreen.html", {
                    "download_type": download_type,
                    "ticker": ticker_value,
                    "market": market_value,
                    "firestore_mode": True,
                    "task_id": task_id,
                    "task_stat": "PENDING",
                    **context_data
                })
            
            elif mode == 'direct':
                # Direct execution completed, show results
                return render(request, "../templates/loadScreen.html", {
                    "download_type": download_type,
                    "ticker": ticker_value,
                    "market": market_value,
                    "firestore_mode": True,
                    "task_id": "direct_execution",
                    **context_data
                })
            
            else:
                return render(request, "../templates/stockData.html", {
                    "error": f"Unknown scraping mode: {mode}"
                })
            
        elif 'download' in request.POST:
            return handle_download_firestore(ticker_value, market_value, download_type)
    
    return render(request, "../templates/stockData.html")

def handle_download_firestore(ticker: str, market: str, download_type: str):
    """Handle data download from Firestore"""
    
    try:
        storage = get_storage()
        
        if download_type == "ALL":
            return handle_all_download_firestore(ticker, market)
        
        # Get data for specific type
        try:
            data_type = DataType(download_type)
        except ValueError:
            return HttpResponse("Invalid download type", status=400)
        
        existing_data = storage.check_data_exists(ticker, market, data_type)
        
        if not existing_data or existing_data['status'] != 'DONE':
            return HttpResponse("No data available for download", status=404)
        
        # Parse and create Excel file
        data = existing_data['data']
        if isinstance(data, str):
            data = json.loads(data)
        
        df = pd.DataFrame(data)
        filename = f"{ticker}_{market}_{download_type.lower()}.xlsx"
        
        # Create response
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        # Write Excel data to response
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=download_type, index=False)
        
        return response
            
    except Exception as e:
        logger.error(f"Error generating download: {str(e)}")
        return HttpResponse(f"Error generating download: {str(e)}", status=500)

def handle_all_download_firestore(ticker: str, market: str):
    """Handle download of all data types for a stock from Firestore"""
    
    try:
        storage = get_storage()
        all_data = storage.get_all_data_for_stock(ticker, market)
        
        if not all_data:
            return HttpResponse("No data available for this stock", status=404)
        
        filename = f"{ticker}_{market}_all_data.xlsx"
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            for data_type, data_info in all_data.items():
                if data_info['status'] == 'DONE':
                    try:
                        data = data_info['data']
                        if isinstance(data, str):
                            data = json.loads(data)
                        df = pd.DataFrame(data)
                        
                        # Clean sheet name (Excel has 31 char limit)
                        sheet_name = data_type.replace('_', ' ').title()[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    except Exception as e:
                        # Create error sheet if data can't be processed
                        error_df = pd.DataFrame({"Error": [f"Could not process data: {str(e)}"]})
                        error_df.to_excel(writer, sheet_name=f"Error_{data_type[:20]}", index=False)
        
        return response
            
    except Exception as e:
        logger.error(f"Error generating comprehensive download: {str(e)}")
        return HttpResponse(f"Error generating comprehensive download: {str(e)}", status=500)

def get_task_info_firestore(request):
    """Enhanced task status endpoint that works with or without Redis/Celery"""
    
    task_id = request.GET.get('task_id', None)
    if not task_id:
        return JsonResponse({
            'state': 'ERROR',
            'result': 'No task ID provided'
        })
    
    # Use the scraping manager to get task status
    from .scraping_manager import get_scraping_manager
    
    scraping_manager = get_scraping_manager()
    data = scraping_manager.get_task_status(task_id)
    
    return JsonResponse(data)

def check_data_status_firestore(request):
    """Check what data exists for a ticker/market combination"""
    
    ticker = request.GET.get('ticker', '').upper()
    market = request.GET.get('market', '').upper()
    
    if not ticker or not market:
        return JsonResponse({
            'error': 'Please provide both ticker and market'
        }, status=400)
    
    try:
        storage = get_storage()
        all_data = storage.get_all_data_for_stock(ticker, market)
        
        data_status = {}
        for data_type in DataType:
            if data_type.value in all_data:
                data_info = all_data[data_type.value]
                data_status[data_type.value] = {
                    'exists': True,
                    'status': data_info['status'],
                    'scraped_at': data_info['scraped_at'].isoformat() if data_info['scraped_at'] else None
                }
            else:
                data_status[data_type.value] = {
                    'exists': False,
                    'status': None,
                    'scraped_at': None
                }
        
        return JsonResponse({
            'ticker': ticker,
            'market': market,
            'data_status': data_status,
            'total_data_types': len([d for d in data_status.values() if d['exists']])
        })
        
    except Exception as e:
        logger.error(f"Error checking data status: {str(e)}")
        return JsonResponse({
            'error': f'Error checking data status: {str(e)}'
        }, status=500)

def storage_stats_firestore(request):
    """Get Firestore storage statistics"""
    
    try:
        storage = get_storage()
        stats = storage.get_storage_stats()
        
        return JsonResponse({
            'storage_stats': stats,
            'storage_type': 'Firestore'
        })
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        return JsonResponse({
            'error': f'Error getting storage stats: {str(e)}'
        }, status=500)

def direct_scrape_firestore(request):
    """Direct scraping endpoint that bypasses task queue"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        ticker = data.get('ticker', '').upper()
        market = data.get('market', '').upper()
        data_type_str = data.get('data_type', '')
        
        if not ticker or not market or not data_type_str:
            return JsonResponse({
                'error': 'Please provide ticker, market, and data_type'
            }, status=400)
        
        try:
            data_type = DataType(data_type_str)
        except ValueError:
            return JsonResponse({
                'error': f'Invalid data type: {data_type_str}'
            }, status=400)
        
        storage = get_storage()
        
        # Check if data already exists
        existing_data = storage.check_data_exists(ticker, market, data_type)
        if existing_data and existing_data['status'] == 'DONE':
            return JsonResponse({
                'status': 'EXISTING',
                'message': 'Data already exists in storage',
                'data': existing_data['data'],
                'scraped_at': existing_data['scraped_at'].isoformat()
            })
        
        # Import and use the appropriate scraping function
        from .tasks_firestore import scrape_financial_statement_firestore
        
        if data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
            result = scrape_financial_statement_firestore(ticker, market, data_type)
            
            if result == 'DONE':
                # Get the newly stored data
                new_data = storage.check_data_exists(ticker, market, data_type)
                return JsonResponse({
                    'status': 'DONE',
                    'message': 'Data scraped and stored successfully',
                    'data': new_data['data'] if new_data else None
                })
            else:
                return JsonResponse({
                    'status': result,
                    'message': f'Scraping completed with status: {result}'
                })
        else:
            return JsonResponse({
                'error': f'Direct scraping not yet implemented for {data_type_str}'
            }, status=501)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        logger.error(f"Error in direct scrape: {str(e)}")
        return JsonResponse({
            'error': f'Error during scraping: {str(e)}'
        }, status=500)

@csrf_exempt
def api_stock_data_firestore(request, ticker, market, data_type_param):
    """
    API endpoint to get specific stock data from Firestore or trigger scraping
    URL format: /api/stock/{ticker}/{market}/{data_type}/
    
    Data type parameters:
    - financialincomestatement -> INCOME_STATEMENT
    - financialbalancesheet -> BALANCE_SHEET
    - financialcashflow -> CASH_FLOW
    - dividends -> DIVIDENDS
    - keymetricscashflow -> KEY_METRICS_CASH_FLOW
    - keymetricsgrowth -> KEY_METRICS_GROWTH
    - keymetricsfinancialhealth -> KEY_METRICS_FINANCIAL_HEALTH
    """
    
    # Normalize inputs
    ticker = ticker.upper()
    market = market.upper()
    
    # Map URL parameter to DataType enum
    data_type_mapping = {
        'financialincomestatement': DataType.INCOME_STATEMENT,
        'financialbalancesheet': DataType.BALANCE_SHEET,
        'financialcashflow': DataType.CASH_FLOW,
        'dividends': DataType.DIVIDENDS,
        'keymetricscashflow': DataType.KEY_METRICS_CASH_FLOW,
        'keymetricsgrowth': DataType.KEY_METRICS_GROWTH,
        'keymetricsfinancialhealth': DataType.KEY_METRICS_FINANCIAL_HEALTH
    }
    
    data_type_param_lower = data_type_param.lower()
    if data_type_param_lower not in data_type_mapping:
        return JsonResponse({
            'error': f'Invalid data type: {data_type_param}',
            'valid_types': list(data_type_mapping.keys())
        }, status=400)
    
    data_type = data_type_mapping[data_type_param_lower]
    
    try:
        storage = get_storage()
        
        # Check if data already exists
        existing_data = storage.check_data_exists(ticker, market, data_type)
        
        if existing_data and existing_data['status'] == 'DONE':
            # Return existing data
            data_json = existing_data['data']
            if isinstance(data_json, str):
                try:
                    data_json = json.loads(data_json)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse stored JSON for {ticker} {market} {data_type.value}")
            
            return JsonResponse({
                'status': 'success',
                'source': 'existing_data',
                'ticker': ticker,
                'market': market,
                'data_type': data_type.value,
                'scraped_at': existing_data['scraped_at'].isoformat(),
                'data': data_json
            })
        
        # Data doesn't exist, trigger scraping
        logger.info(f"No existing data for {ticker} {market} {data_type.value} - starting scrape")
        
        # Trigger appropriate scraper based on data type
        if data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
            from .tasks_firestore import scrape_financial_statement_firestore
            result = scrape_financial_statement_firestore(ticker, market, data_type)
        elif data_type == DataType.DIVIDENDS:
            # For dividends, we need to implement a sync version
            result = scrape_dividends_direct(ticker, market)
        elif data_type in [DataType.KEY_METRICS_CASH_FLOW, DataType.KEY_METRICS_GROWTH, DataType.KEY_METRICS_FINANCIAL_HEALTH]:
            # For key metrics, we need to implement a sync version
            result = scrape_key_metrics_direct(ticker, market, data_type)
        else:
            return JsonResponse({
                'error': f'Scraping not implemented for {data_type.value}'
            }, status=501)
        
        if result == 'EXISTING':
            # Data was found during scraping (race condition)
            new_data = storage.check_data_exists(ticker, market, data_type)
            data_json = new_data['data']
            if isinstance(data_json, str):
                try:
                    data_json = json.loads(data_json)
                except json.JSONDecodeError:
                    pass
            
            return JsonResponse({
                'status': 'success',
                'source': 'existing_data',
                'ticker': ticker,
                'market': market,
                'data_type': data_type.value,
                'scraped_at': new_data['scraped_at'].isoformat(),
                'data': data_json
            })
        
        elif result == 'DONE':
            # Successfully scraped new data
            new_data = storage.check_data_exists(ticker, market, data_type)
            data_json = new_data['data']
            if isinstance(data_json, str):
                try:
                    data_json = json.loads(data_json)
                except json.JSONDecodeError:
                    pass
            
            return JsonResponse({
                'status': 'success',
                'source': 'newly_scraped',
                'ticker': ticker,
                'market': market,
                'data_type': data_type.value,
                'scraped_at': new_data['scraped_at'].isoformat(),
                'data': data_json
            })
        
        else:
            # Scraping failed or returned partial data
            return JsonResponse({
                'status': 'error',
                'message': f'Scraping failed with result: {result}',
                'ticker': ticker,
                'market': market,
                'data_type': data_type.value
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in API endpoint: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Internal server error: {str(e)}',
            'ticker': ticker,
            'market': market,
            'data_type': data_type.value
        }, status=500) 