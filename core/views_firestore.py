from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
from .firestore_storage import (
    DataType,
    get_storage,
)
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
                                   "KEY_METRICS_FINANCIAL_HEALTH"]:
                from .tasks_firestore import key_metrics_firestore_check  
                task = key_metrics_firestore_check.delay(ticker_value, market_value, download_type)
            elif download_type == "DIVIDENDS":
                from .tasks_firestore import dividends_firestore_check
                task = dividends_firestore_check.delay(ticker_value, market_value)
            elif download_type == "ALL":
                from .tasks_firestore import all_scraper_firestore
                task = all_scraper_firestore.delay(ticker_value, market_value)
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
            from .tasks_firestore import scraper_financial_statement
            result = scraper_financial_statement(ticker, market, data_type)
        elif data_type == DataType.DIVIDENDS:
            # For dividends, we need to implement a sync version
            from .tasks_firestore import scraper_dividends
            result = scraper_dividends(ticker, market, data_type)
        elif data_type in [DataType.KEY_METRICS_CASH_FLOW, DataType.KEY_METRICS_GROWTH, DataType.KEY_METRICS_FINANCIAL_HEALTH]:
            # For key metrics, we need to implement a sync version
            from .tasks_firestore import scraper_key_metrics
            result = scraper_key_metrics(ticker, market, data_type)
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