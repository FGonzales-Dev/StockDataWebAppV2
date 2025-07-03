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
    scraper_financial_statement,
    scraper_key_metrics,
    scraper_dividends
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

            if download_type == "ALL":
                from .tasks_firestore import all_scraper_firestore
                task = all_scraper_firestore.delay(ticker_value, market_value)
                return render(request, "../templates/loadScreen.html", {
                    "download_type": download_type,
                    "task_id": task.id,
                    "task_stat": task.status,
                    "ticker": ticker_value,
                    "market": market_value,
                    "firestore_mode": True
                })
            
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
            
            # Data doesn't exist, start background scraping and show loading screen
            logger.info(f"No existing data found for {ticker_value} {market_value} {download_type} - starting background scrape")
            
            # Create a background task for scraping
            if download_type in ["INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW"]:
                from .tasks_firestore import financial_statement_firestore_check
                task = financial_statement_firestore_check.delay(ticker_value, market_value, download_type)
            elif download_type in ["KEY_METRICS_CASH_FLOW", "KEY_METRICS_GROWTH", 
                                   "KEY_METRICS_FINANCIAL_HEALTH", "KEY_METRICS_PROFITABILITYANDEFFICIENCY", "KEY_METRICS_FINANCIAL_SUMMARY"]:
                from .tasks_firestore import key_metrics_firestore_check  
                task = key_metrics_firestore_check.delay(ticker_value, market_value, download_type)
            elif download_type == "DIVIDENDS":
                from .tasks_firestore import dividends_firestore_check
                task = dividends_firestore_check.delay(ticker_value, market_value)
            else:
                return render(request, "../templates/stockData.html", {
                    "error": f"Unsupported download type: {download_type}"
                })
            
            # Return loading screen immediately with task ID
            return render(request, "../templates/loadScreen.html", {
                "download_type": download_type,
                "task_id": task.id,
                "task_stat": task.status,
                "ticker": ticker_value,
                "market": market_value,
                "firestore_mode": True  # Flag to indicate this is firestore scraping
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
            # Clean sheet name (Excel has 31 char limit)
            sheet_name = download_type.replace('_', ' ').title()[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
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
    """Enhanced task status endpoint for Firestore tasks"""
    
    task_id = request.GET.get('task_id', None)
    if not task_id:
        return JsonResponse({
            'state': 'ERROR',
            'result': 'No task ID provided'
        })
    
    try:
        task = AsyncResult(task_id)
        data = {
            'state': task.state,
            'result': task.result,
            'firestore': True  # Flag to indicate this is from Firestore scraper
        }
        
        # Add additional info based on task state
        if task.state == 'PROGRESS':
            # Handle progress updates
            if isinstance(task.result, dict):
                data['progress'] = task.result.get('progress', 0)
                data['current'] = task.result.get('current', 0)
                data['total'] = task.result.get('total', 1)
                data['message'] = task.result.get('message', 'Processing...')
            else:
                data['progress'] = 50  # Default progress
                data['message'] = 'Scraping in progress...'
                
        elif task.state == 'SUCCESS':
            if isinstance(task.result, str):
                if task.result == 'EXISTING':
                    data['message'] = 'Data already existed in Firestore storage'
                    data['result'] = 'EXISTING'
                elif task.result == 'DONE':
                    data['message'] = 'Data scraped and stored successfully in Firestore'
                    data['result'] = 'DONE'
                elif task.result == 'PARTIAL':
                    data['message'] = 'Data partially scraped and stored in Firestore'
                    data['result'] = 'PARTIAL'
                else:
                    data['message'] = f'Task completed with result: {task.result}'
            elif isinstance(task.result, dict):
                data['results'] = task.result
                data['message'] = 'Task completed successfully'
            else:
                data['message'] = 'Task completed successfully'
                
        elif task.state == 'FAILURE':
            data['error'] = str(task.result)
            data['message'] = f'Task failed: {str(task.result)}'
            
        elif task.state == 'PENDING':
            data['message'] = 'Task is waiting to be processed'
            data['progress'] = 0
            
        elif task.state == 'STARTED':
            data['message'] = 'Task is being processed'
            data['progress'] = 25
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'state': 'ERROR',
            'result': f'Error retrieving task info: {str(e)}',
            'message': f'Error retrieving task info: {str(e)}'
        })

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

@csrf_exempt
def api_stock_data_firestore(request, ticker, market, data_type_param):
    """
    API endpoint to get specific stock data from Firestore or trigger scraping
    URL format: /api/stock/{ticker}/{market}/{data_type}/
    
    Data type parameters:
    - incomestatement -> INCOME_STATEMENT
    - balance_sheet -> BALANCE_SHEET
    - cash_flow -> CASH_FLOW
    - dividends -> DIVIDENDS
    - key_metrics_cash_flow -> KEY_METRICS_CASH_FLOW
    - key_metrics_growth -> KEY_METRICS_GROWTH
    - key_metrics_financial_health -> KEY_METRICS_FINANCIAL_HEALTH
    - key_metrics_profitability_and_efficiency -> KEY_METRICS_PROFITABILITYANDEFFICIENCY
    - key_metrics_financial_summary -> KEY_METRICS_FINANCIAL_SUMMARY
    """
    
    # Normalize inputs
    ticker = ticker.upper()
    market = market.upper()
    
    # Map URL parameter to DataType enum
    data_type_mapping = {
        'incomestatement': DataType.INCOME_STATEMENT,
        'balance_sheet': DataType.BALANCE_SHEET,
        'cash_flow': DataType.CASH_FLOW,
        'dividends': DataType.DIVIDENDS,
        'key_metrics_cash_flow': DataType.KEY_METRICS_CASH_FLOW,
        'key_metrics_growth': DataType.KEY_METRICS_GROWTH,
        'key_metrics_financial_health': DataType.KEY_METRICS_FINANCIAL_HEALTH,
        'key_metrics_profitability_and_efficiency': DataType.KEY_METRICS_PROFITABILITYANDEFFICIENCY,
        'key_metrics_financial_summary': DataType.KEY_METRICS_FINANCIAL_SUMMARY
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
                'scraped_at': existing_data['scraped_at'].isoformat() if existing_data['scraped_at'] else None,
                'data': data_json
            })
        
        # Data doesn't exist, trigger scraping
        logger.info(f"No existing data for {ticker} {market} {data_type.value} - starting scrape")
        
        # Trigger appropriate scraper based on data type
        if data_type in [DataType.INCOME_STATEMENT, DataType.BALANCE_SHEET, DataType.CASH_FLOW]:
            from .tasks_firestore import financial_statement_firestore_check
            task = financial_statement_firestore_check.delay(ticker, market, data_type.value)
        elif data_type == DataType.DIVIDENDS:
            from .tasks_firestore import dividends_firestore_check
            task = dividends_firestore_check.delay(ticker, market)
        elif data_type in [DataType.KEY_METRICS_CASH_FLOW, DataType.KEY_METRICS_GROWTH, DataType.KEY_METRICS_FINANCIAL_HEALTH, DataType.KEY_METRICS_PROFITABILITYANDEFFICIENCY, DataType.KEY_METRICS_FINANCIAL_SUMMARY]:
            from .tasks_firestore import key_metrics_firestore_check
            task = key_metrics_firestore_check.delay(ticker, market, data_type.value)
        else:
            return JsonResponse({
                'error': f'Scraping not implemented for {data_type.value}'
            }, status=501)
        
        # Return task information
        return JsonResponse({
            'status': 'pending',
            'message': 'Data scraping initiated',
            'ticker': ticker,
            'market': market,
            'data_type': data_type.value,
            'task_id': task.id,
            'task_status': task.status
        })
            
    except Exception as e:
        logger.error(f"Error in API endpoint: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Internal server error: {str(e)}',
            'ticker': ticker,
            'market': market,
            'data_type': data_type.value
        }, status=500) 