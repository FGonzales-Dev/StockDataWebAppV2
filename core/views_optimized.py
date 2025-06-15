"""
Optimized Views for Stock Data Scraping
Direct integration with OptimizedScraper class
"""

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
from .scraper_optimized import OptimizedScraper, DataType, ScrapingConfig
from .tasks_optimized import (
    scraper_optimized, 
    scraper_dividends_optimized, 
    scraper_valuation_optimized, 
    scraper_operating_performance_optimized, 
    all_scraper_optimized
)
from celery.result import AsyncResult
import pyrebase

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyD7fxurFiXK0agVyqr1wnfhnymIRCRiPXY",
    "authDomain": "scraper-b0a07.firebaseapp.com",
    "projectId": "scraper-b0a07",
    "storageBucket": "scraper-b0a07.appspot.com",
    "messagingSenderId": "1066439876574",
    "appId": "1:1066439876574:web:d0d4366594823a2d7f874f",
    "measurementId": "G-TJTZ8ZT9CW",
    "databaseURL": "https://scraper-b0a07-default-rtdb.asia-southeast1.firebasedatabase.app"
}

firebase = pyrebase.initialize_app(firebase_config)
database = firebase.database()

@csrf_exempt
def scrape_optimized(request):
    """Optimized scraping endpoint with better performance and error handling"""
    
    if request.method == 'POST':
        ticker_value = request.POST.get("ticker", "")
        market_value = request.POST.get("market", "")
        download_type = request.POST.get("download_type", "")
        
        # Clear download directory
        scraper = OptimizedScraper()
        scraper.cleanup_download_directory()
        
        if 'get_data' in request.POST:
            # Route to appropriate optimized task
            if download_type in ["INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW"]:
                task = scraper_optimized.delay(
                    ticker_value=ticker_value, 
                    market_value=market_value, 
                    download_type=download_type
                )
            elif download_type in ["VALUATION_CASH_FLOW", "VALUATION_GROWTH", 
                                   "VALUATION_FINANCIAL_HEALTH", "VALUATION_OPERATING_EFFICIENCY"]:
                task = scraper_valuation_optimized.delay(
                    ticker_value=ticker_value, 
                    market_value=market_value, 
                    download_type=download_type
                )
            elif download_type == "DIVIDENDS":
                task = scraper_dividends_optimized.delay(
                    ticker_value=ticker_value, 
                    market_value=market_value
                )
            elif download_type == "OPERATING_PERFORMANCE":
                task = scraper_operating_performance_optimized.delay(
                    ticker_value=ticker_value, 
                    market_value=market_value
                )
            elif download_type == "ALL":
                task = all_scraper_optimized.delay(
                    ticker_value=ticker_value, 
                    market_value=market_value
                )
            else:
                return render(request, "../templates/stockData.html", {
                    "error": f"Unsupported download type: {download_type}"
                })
            
            return render(request, "../templates/loadScreen.html", {
                "download_type": download_type,
                "task_id": task.id, 
                "task_stat": task.status,
                "optimized": True  # Flag to indicate optimized scraper
            })
            
        elif 'download' in request.POST:
            return handle_download_optimized(download_type)
    
    return render(request, "../templates/stockData.html")

def handle_download_optimized(download_type):
    """Handle data download with improved error handling"""
    
    try:
        # Map download types to database keys
        db_key_map = {
            "INCOME_STATEMENT": "income_statement",
            "BALANCE_SHEET": "balance_sheet",
            "CASH_FLOW": "cash_flow",
            "DIVIDENDS": "dividends",
            "OPERATING_PERFORMANCE": "operating_performance",
            "VALUATION_CASH_FLOW": "valuation_cash_flow",
            "VALUATION_GROWTH": "valuation_growth",
            "VALUATION_FINANCIAL_HEALTH": "valuation_financial_health",
            "VALUATION_OPERATING_EFFICIENCY": "valuation_operating_efficiency"
        }
        
        if download_type == "ALL":
            return handle_all_download_optimized()
        
        if download_type not in db_key_map:
            return HttpResponse("Invalid download type", status=400)
        
        db_key = db_key_map[download_type]
        data = database.child(db_key).child(db_key).get().val()
        
        if not data:
            return HttpResponse("No data available", status=404)
        
        # Parse and create Excel file
        if isinstance(data, str):
            data = json.loads(data)
        
        df = pd.DataFrame(data)
        filename = f"{download_type.lower()}.xlsx"
        
        df.to_excel(filename, index=False)
        
        with open(filename, 'rb') as file:
            response = HttpResponse(file, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
            
    except Exception as e:
        return HttpResponse(f"Error generating download: {str(e)}", status=500)

def handle_all_download_optimized():
    """Handle download of all data types in a single Excel file"""
    
    try:
        data_types = [
            ("income_statement", "Income Statement"),
            ("balance_sheet", "Balance Sheet"),
            ("cash_flow", "Cash Flow"),
            ("dividends", "Dividends"),
            ("valuation_cash_flow", "Valuation Cash Flow"),
            ("valuation_growth", "Valuation Growth"),
            ("valuation_financial_health", "Valuation Financial Health"),
            ("valuation_operating_efficiency", "Valuation Operating Efficiency"),
            ("operating_performance", "Operating Performance")
        ]
        
        writer = pd.ExcelWriter("all_data_optimized.xlsx", engine='xlsxwriter')
        
        for db_key, sheet_name in data_types:
            try:
                data = database.child(db_key).child(db_key).get().val()
                if data:
                    if isinstance(data, str):
                        data = json.loads(data)
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception as e:
                # Create empty sheet if data not available
                pd.DataFrame({"Error": [f"No data available: {str(e)}"]}).to_excel(
                    writer, sheet_name=sheet_name, index=False
                )
        
        writer.close()
        
        with open("all_data_optimized.xlsx", 'rb') as file:
            response = HttpResponse(file, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=all_stock_data.xlsx'
            return response
            
    except Exception as e:
        return HttpResponse(f"Error generating comprehensive download: {str(e)}", status=500)

def get_task_info_optimized(request):
    """Enhanced task status endpoint with better error reporting"""
    
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
            'optimized': True  # Flag to indicate this is from optimized scraper
        }
        
        # Enhanced status information
        status_messages = {
            'FAILURE': 'Task failed. Please check the ticker symbol and try again.',
            'SUCCESS': 'Task completed successfully! Data is ready for download.',
            'PENDING': 'Task is waiting to be processed...',
            'STARTED': 'Task is being processed. Please wait...',
            'RETRY': 'Task is retrying after an error...',
            'REVOKED': 'Task was cancelled.'
        }
        
        data['message'] = status_messages.get(task.state, 'Unknown status')
        
        if task.state == 'FAILURE':
            if hasattr(task.result, 'args') and task.result.args:
                data['result'] = str(task.result.args[0])
            else:
                data['result'] = str(task.result)
                
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'state': 'ERROR',
            'result': f'Error retrieving task status: {str(e)}',
            'optimized': True
        })

# Direct scraper usage (for testing or API endpoints)
def direct_scrape_optimized(request):
    """Direct scraping without Celery (for testing purposes)"""
    
    if request.method == 'POST':
        ticker = request.POST.get("ticker", "")
        market = request.POST.get("market", "")
        data_type_str = request.POST.get("download_type", "")
        
        try:
            data_type = DataType(data_type_str)
            scraper = OptimizedScraper()
            result = scraper.scrape_financial_data(ticker, market, data_type)
            
            return JsonResponse({
                'status': result,
                'ticker': ticker,
                'market': market,
                'data_type': data_type_str,
                'optimized': True
            })
            
        except ValueError:
            return JsonResponse({
                'status': 'ERROR',
                'error': f'Invalid data type: {data_type_str}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'ERROR',
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'POST method required'}, status=405) 