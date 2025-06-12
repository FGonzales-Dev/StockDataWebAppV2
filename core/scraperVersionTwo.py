from operator import index
import os
from zlib import DEF_BUF_SIZE
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from django.http import HttpResponseRedirect
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from stock_scraper.settings import BASE_DIR, STATIC_ROOT
import shutil
from webdriver_manager.chrome import ChromeDriverManager
from django.http import FileResponse
from pathlib import Path
import shutil
from bs4 import BeautifulSoup
import string
import io
from time import sleep
from email import header
from core.forms import getDataForm
import xlsxwriter
import openpyxl
from openpyxl import workbook
from openpyxl.styles import *

# Resource monitoring imports
import psutil
import time
from datetime import datetime
import logging

from core.views import get_balance_sheet
from requests.structures import CaseInsensitiveDict
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.shortcuts import render,redirect
import requests
import json 
import threading
from typing import List, final
from collections.abc import Iterable
from django.http import HttpResponse
import re
from bs4 import BeautifulSoup
import csv
import pandas as pd
from json import loads
import requests
from time import sleep
import glob
from django.http import JsonResponse

from .models import APIRequest
from register.models import Profile
from django.contrib.auth.models import User
from .tasks import *
import ast
from celery.result import AsyncResult


import pyrebase
import os

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
storage = firebase.storage()
database =firebase.database()


def get_task_info(request):
    task_id = request.GET.get('task_id', None)
    if task_id is not None:
        try:
            # Initialize Celery app for production
            from stock_scraper.celery import app as celery_app
            task = AsyncResult(task_id, app=celery_app)
            
            print(f"[DEBUG] Task ID: {task_id}")
            print(f"[DEBUG] Task state: {task.state}")
            print(f"[DEBUG] Task result: {task.result}")
            
            data = {
                'state': task.state,
                'result': task.result,
            }
            
            # Add more detailed information based on task state
            if task.state == 'FAILURE':
                # Get the exception information if available
                if hasattr(task.result, 'args') and task.result.args:
                    data['result'] = str(task.result.args[0])
                else:
                    data['result'] = str(task.result)
            elif task.state == 'SUCCESS':
                data['result'] = 'Task completed successfully'
            elif task.state == 'PENDING':
                data['result'] = 'Task is waiting to be processed'
            elif task.state == 'STARTED':
                data['result'] = 'Task is being processed'
                
            print(f"[DEBUG] Returning data: {data}")
            return JsonResponse(data)
        except Exception as e:
            print(f"[ERROR] Exception in get_task_info: {str(e)}")
            return JsonResponse({
                'state': 'ERROR',
                'result': f'Error retrieving task status: {str(e)}'
            })
    else:
        return JsonResponse({
            'state': 'ERROR',
            'result': 'No task ID provided'
        })


def download(request):
    return render(request, "../templates/loadScreen.html")

def remove_whitespaces(d):
    new_dict = {}
    for key, value in d.items():
        key = key.strip()
        if isinstance(value, str):
            value = value.strip()
        elif isinstance(value, dict):
            value = remove_whitespaces(value)
        new_dict[key] = value
    return new_dict

def clear_selenium_directory():
    DOWNLOAD_DIRECTORY = "/selenium"
    selenium_dir = BASE_DIR + DOWNLOAD_DIRECTORY
    
    if os.path.exists(selenium_dir):
        for filename in os.listdir(selenium_dir):
            file_path = os.path.join(selenium_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

class ResourceMonitor:
    """Monitor CPU and Memory usage during scraping operations"""
    
    def __init__(self, operation_name=""):
        self.operation_name = operation_name
        self.process = psutil.Process()
        self.start_time = None
        self.start_memory = None
        self.start_cpu_percent = None
        self.peak_memory = 0
        self.peak_cpu = 0
        
    def start_monitoring(self):
        """Start monitoring resources"""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_cpu_percent = self.process.cpu_percent()
        self.peak_memory = self.start_memory
        self.peak_cpu = self.start_cpu_percent
        
        print(f"🔍 [{self.operation_name}] Starting resource monitoring:")
        print(f"   Initial Memory: {self.start_memory:.2f} MB")
        print(f"   Initial CPU: {self.start_cpu_percent:.1f}%")
        
    def update_peaks(self):
        """Update peak resource usage"""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        current_cpu = self.process.cpu_percent()
        
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        if current_cpu > self.peak_cpu:
            self.peak_cpu = current_cpu
            
    def end_monitoring(self):
        """End monitoring and return summary"""
        if self.start_time is None:
            return None
            
        end_time = time.time()
        duration = end_time - self.start_time
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = self.process.cpu_percent()
        
        # Update peaks one final time
        self.update_peaks()
        
        memory_diff = end_memory - self.start_memory
        
        summary = {
            'operation': self.operation_name,
            'duration_seconds': round(duration, 2),
            'start_memory_mb': round(self.start_memory, 2),
            'end_memory_mb': round(end_memory, 2),
            'peak_memory_mb': round(self.peak_memory, 2),
            'memory_diff_mb': round(memory_diff, 2),
            'peak_cpu_percent': round(self.peak_cpu, 1),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"📊 [{self.operation_name}] Resource Usage Summary:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Memory: {self.start_memory:.2f} → {end_memory:.2f} MB (Δ{memory_diff:+.2f} MB)")
        print(f"   Peak Memory: {self.peak_memory:.2f} MB")
        print(f"   Peak CPU: {self.peak_cpu:.1f}%")
        print(f"   Timestamp: {summary['timestamp']}")
        
        # Log to file for analysis
        self.log_to_file(summary)
        
        return summary
        
    def log_to_file(self, summary):
        """Log resource usage to file"""
        try:
            log_file = os.path.join(BASE_DIR, 'resource_usage.log')
            with open(log_file, 'a') as f:
                f.write(f"{json.dumps(summary)}\n")
        except Exception as e:
            print(f"Failed to log resource usage: {e}")

def monitor_scraping_resources(func):
    """Decorator to monitor resource usage of scraping functions"""
    def wrapper(*args, **kwargs):
        # Extract operation info from args/kwargs
        operation_name = func.__name__
        if len(args) > 0 and hasattr(args[0], 'POST'):
            # Django request object
            ticker = args[0].POST.get('ticker', 'Unknown')
            download_type = args[0].POST.get('download_type', 'Unknown')
            operation_name = f"{func.__name__}_{ticker}_{download_type}"
        
        monitor = ResourceMonitor(operation_name)
        monitor.start_monitoring()
        
        try:
            # Periodically update peaks during execution
            import threading
            def update_monitor():
                while not getattr(threading.current_thread(), 'stop', False):
                    monitor.update_peaks()
                    time.sleep(1)  # Update every second
            
            monitor_thread = threading.Thread(target=update_monitor)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            result = func(*args, **kwargs)
            
            # Stop the monitoring thread
            monitor_thread.stop = True
            monitor_thread.join(timeout=1)
            
            return result
        finally:
            monitor.end_monitoring()
    
    return wrapper

@monitor_scraping_resources
def scrape(request):
    # Handle GET requests (homepage visits) vs POST requests (form submissions)
    if request.method == 'GET':
        # Show the main form page for GET requests
        return render(request, "../templates/stockData.html")
    
    # Handle POST requests (form submissions)
    clear_selenium_directory()

    ticker_value =  request.POST.get("ticker", "")
    market_value =  request.POST.get("market", "")
    download_type = request.POST.get("download_type", "")
    task_id = request.POST.get("task_id", "")
    if 'get_data' in request.POST:
        if download_type == "INCOME_STATEMENT" or download_type == "BALANCE_SHEET" or download_type == "CASH_FLOW":
            task = scraper.delay(ticker_value=ticker_value, market_value=market_value, download_type=download_type)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type == "KEY_METRICS_CASH_FLOW" or download_type == "KEY_METRICS_GROWTH" or download_type == "KEY_METRICS_FINANCIAL_HEALTH" or download_type == "VALUATION_OPERATING_EFFICIENCY":
            task = scraper_valuation.delay(ticker_value=ticker_value, market_value=market_value, download_type=download_type)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type =="DIVIDENDS":
            task = scraper_dividends.delay(ticker_value=ticker_value, market_value=market_value)
            dividends_task_id = task.id
            print(dividends_task_id)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type == "VALUATION":
            task = scraper.delay(ticker_value=ticker_value, market_value=market_value, download_type=download_type)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        # elif download_type == "OPERATING_PERFORMANCE":
        #     task = scraper_operating_performance.delay(ticker_value=ticker_value, market_value=market_value)
        #     return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type == "ALL":
            task = all_scraper.delay(ticker_value=ticker_value, market_value=market_value)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        else:
            return render(request, "../templates/stockData.html")
    elif 'download' in request.POST:
        # Create ticker-specific database key
        db_key_prefix = f"{ticker_value}_{market_value}"
        
        if download_type == "INCOME_STATEMENT": 
            income_statement_data = database.child('income_statement').child(db_key_prefix).get().val()
            if income_statement_data:
                income_statement_data = json.loads(income_statement_data)
                new_dict = remove_whitespaces(income_statement_data)
                df = pd.DataFrame(new_dict).to_excel("income_statement.xlsx", index=False)
                with open("income_statement.xlsx", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                    return response
            else:
                # No data found for this ticker
                df_no_data = pd.DataFrame({"Message": [f"No income statement data available for {ticker_value}"]})
                df_no_data.to_excel("no_data.xlsx", index=False)
                with open("no_data.xlsx", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                    return response
        elif download_type == "BALANCE_SHEET":
            balance_sheet_data = database.child('balance_sheet').child(db_key_prefix).get().val()
            if balance_sheet_data:
                balance_sheet_data = json.loads(balance_sheet_data)
                new_dict = remove_whitespaces(balance_sheet_data)  
                df = pd.DataFrame(new_dict).to_excel("balance_sheet.xlsx", index=False)
                with open("balance_sheet.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'  
                        return response
            else:
                # No data found for this ticker
                df_no_data = pd.DataFrame({"Message": [f"No balance sheet data available for {ticker_value}"]})
                df_no_data.to_excel("no_data.xlsx", index=False)
                with open("no_data.xlsx", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                    return response
        elif download_type == "CASH_FLOW":
                cash_flow_data = database.child('cash_flow').child(db_key_prefix).get().val()
                if cash_flow_data:
                    cash_flow_data = json.loads(cash_flow_data)
                    new_dict = remove_whitespaces(cash_flow_data)  
                    df = pd.DataFrame(new_dict).to_excel("cash_flow.xlsx", index=False)
                    with open("cash_flow.xlsx", 'rb') as file:
                            response = HttpResponse(file, content_type='application/vnd.ms-excel')
                            response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                            return response
                else:
                    # No data found for this ticker
                    df_no_data = pd.DataFrame({"Message": [f"No cash flow data available for {ticker_value}"]})
                    df_no_data.to_excel("no_data.xlsx", index=False)
                    with open("no_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                        return response
        elif download_type == "DIVIDENDS":
            dividends_data = database.child('dividends').child(db_key_prefix).get().val()
            if dividends_data:
                dividends_data = json.loads(dividends_data)
                print(dividends_data)
                df = pd.DataFrame(dividends_data).to_excel("dividends_data.xlsx", index=False)
                with open("dividends_data.xlsx", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                    return response
            else:
                df_no_data = pd.DataFrame({"Message": [f"No dividends data available for {ticker_value}"]})
                df_no_data.to_excel("no_data.xlsx", index=False)
                with open("no_data.xlsx", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                    return response
        elif download_type == "OPERATING_PERFORMANCE":
                operating_performance_data = database.child('operating_performance').child(db_key_prefix).get().val()
                if operating_performance_data:
                    operating_performance_data = json.loads(operating_performance_data)
                    print(operating_performance_data)
                    df = pd.DataFrame(operating_performance_data).to_excel("operating_performance.xlsx", index=False)
                    with open("operating_performance.xlsx", 'rb') as file:
                            response = HttpResponse(file, content_type='application/vnd.ms-excel')
                            response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                            return response
                else:
                    df_no_data = pd.DataFrame({"Message": [f"No operating performance data available for {ticker_value}"]})
                    df_no_data.to_excel("no_data.xlsx", index=False)
                    with open("no_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                        return response
        elif download_type == "KEY_METRICS_CASH_FLOW":
                valuation_cash_flow_data = database.child('valuation_cash_flow').child(db_key_prefix).get().val()
                if valuation_cash_flow_data:
                    valuation_cash_flow_data = json.loads(valuation_cash_flow_data)
                    print(valuation_cash_flow_data)
                    df = pd.DataFrame(valuation_cash_flow_data).to_excel("valuation_cash_flow.xlsx", index=False)
                    with open("valuation_cash_flow.xlsx", 'rb') as file:
                            response = HttpResponse(file, content_type='application/vnd.ms-excel')
                            response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                            return response
                else:
                    df_no_data = pd.DataFrame({"Message": [f"No key metrics cash flow data available for {ticker_value}"]})
                    df_no_data.to_excel("no_data.xlsx", index=False)
                    with open("no_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                        return response
        elif download_type == "KEY_METRICS_GROWTH":
                valuation_growth_data = database.child('valuation_growth').child(db_key_prefix).get().val()
                if valuation_growth_data:
                    valuation_growth_data = json.loads(valuation_growth_data)
                    print(valuation_growth_data)
                    df = pd.DataFrame(valuation_growth_data).to_excel("valuation_growth.xlsx", index=False)
                    with open("valuation_growth.xlsx", 'rb') as file:
                            response = HttpResponse(file, content_type='application/vnd.ms-excel')
                            response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                            return response
                else:
                    df_no_data = pd.DataFrame({"Message": [f"No key metrics growth data available for {ticker_value}"]})
                    df_no_data.to_excel("no_data.xlsx", index=False)
                    with open("no_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                        return response
        elif download_type == "KEY_METRICS_FINANCIAL_HEALTH":
                valuation_financial_health_data = database.child('valuation_financial_health').child(db_key_prefix).get().val()
                if valuation_financial_health_data:
                    valuation_financial_health_data = json.loads(valuation_financial_health_data)
                    print(valuation_financial_health_data)
                    df = pd.DataFrame(valuation_financial_health_data).to_excel("valuation_financial_health.xlsx", index=False)
                    with open("valuation_financial_health.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                        return response
                else:
                    df_no_data = pd.DataFrame({"Message": [f"No key metrics financial health data available for {ticker_value}"]})
                    df_no_data.to_excel("no_data.xlsx", index=False)
                    with open("no_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                        return response
        elif download_type == "VALUATION_OPERATING_EFFICIENCY":
                valuation_operating_efficiency_data = database.child('valuation_operating_efficiency').child(db_key_prefix).get().val()
                if valuation_operating_efficiency_data:
                    valuation_operating_efficiency_data = json.loads(valuation_operating_efficiency_data)
                    print(valuation_operating_efficiency_data)
                    df = pd.DataFrame(valuation_operating_efficiency_data).to_excel("valuation_operating_efficiency.xlsx", index=False)
                    with open("valuation_operating_efficiency.xlsx", 'rb') as file:
                            response = HttpResponse(file, content_type='application/vnd.ms-excel')
                            response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                            return response
                else:
                    df_no_data = pd.DataFrame({"Message": [f"No valuation operating efficiency data available for {ticker_value}"]})
                    df_no_data.to_excel("no_data.xlsx", index=False)
                    with open("no_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                        return response
        elif download_type == "VALUATION":
                valuation_data = database.child('valuation').child(db_key_prefix).get().val()
                if valuation_data:
                    valuation_data = json.loads(valuation_data)
                    print(valuation_data)
                    df = pd.DataFrame(valuation_data).to_excel("valuation.xlsx", index=False)
                    with open("valuation.xlsx", 'rb') as file:
                            response = HttpResponse(file, content_type='application/vnd.ms-excel')
                            response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                            return response
                else:
                    df_no_data = pd.DataFrame({"Message": [f"No valuation data available for {ticker_value}"]})
                    df_no_data.to_excel("no_data.xlsx", index=False)
                    with open("no_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=no_data.xlsx'   
                        return response
        elif download_type == "ALL":
            # Create comprehensive Excel file with all scraped data for this specific ticker
            dataframes = {}
            
            try:
                # INCOME STATEMENT
                try:
                    income_statement_data = database.child('income_statement').child(db_key_prefix).get().val()
                    if income_statement_data and income_statement_data != '{"income_statement":{"none":"no data"}}':
                        income_statement_data = json.loads(income_statement_data)
                        new_dict = remove_whitespaces(income_statement_data)  
                        df1 = pd.DataFrame(new_dict)
                        dataframes['Income Statement'] = df1
                        print(f"✅ Income Statement data loaded for {ticker_value} ALL export")
                    else:
                        print(f"❌ No Income Statement data available for {ticker_value}")
                except Exception as e:
                    print(f"❌ Error loading Income Statement for {ticker_value}: {e}")
                
                # BALANCE SHEET
                try:
                    balance_sheet_data = database.child('balance_sheet').child(db_key_prefix).get().val()
                    if balance_sheet_data and balance_sheet_data != '{"balance_sheet":{"none":"no data"}}':
                        balance_sheet_data = json.loads(balance_sheet_data)
                        new_dict = remove_whitespaces(balance_sheet_data)  
                        df2 = pd.DataFrame(new_dict)
                        dataframes['Balance Sheet'] = df2
                        print(f"✅ Balance Sheet data loaded for {ticker_value} ALL export")
                    else:
                        print(f"❌ No Balance Sheet data available for {ticker_value}")
                except Exception as e:
                    print(f"❌ Error loading Balance Sheet for {ticker_value}: {e}")
                
                # CASH FLOW
                try:
                    cash_flow_data = database.child('cash_flow').child(db_key_prefix).get().val()
                    if cash_flow_data and cash_flow_data != '{"cash_flow":{"none":"no data"}}':
                        cash_flow_data = json.loads(cash_flow_data)
                        new_dict = remove_whitespaces(cash_flow_data)  
                        df3 = pd.DataFrame(new_dict)
                        dataframes['Cash Flow'] = df3
                        print(f"✅ Cash Flow data loaded for {ticker_value} ALL export")
                    else:
                        print(f"❌ No Cash Flow data available for {ticker_value}")
                except Exception as e:
                    print(f"❌ Error loading Cash Flow for {ticker_value}: {e}")
                
                # DIVIDENDS
                try:
                    dividends_data = database.child('dividends').child(db_key_prefix).get().val()
                    if dividends_data and dividends_data != '{"dividends":{"none":"no data"}}':
                        dividends_data = json.loads(dividends_data)
                        df4 = pd.DataFrame(dividends_data)
                        dataframes['Dividends'] = df4
                        print(f"✅ Dividends data loaded for {ticker_value} ALL export")
                    else:
                        print(f"❌ No Dividends data available for {ticker_value}")
                except Exception as e:
                    print(f"❌ Error loading Dividends for {ticker_value}: {e}")

                # KEY METRICS CASH FLOW
                try:
                    valuation_cash_flow_data = database.child('valuation_cash_flow').child(db_key_prefix).get().val()
                    if valuation_cash_flow_data and valuation_cash_flow_data != '{"valuation_cash_flow":{"none":"no data"}}':
                        valuation_cash_flow_data = json.loads(valuation_cash_flow_data)
                        df5 = pd.DataFrame(valuation_cash_flow_data)
                        dataframes['Key Metrics Cash Flow'] = df5
                        print(f"✅ Key Metrics Cash Flow data loaded for {ticker_value} ALL export")
                    else:
                        print(f"❌ No Key Metrics Cash Flow data available for {ticker_value}")
                except Exception as e:
                    print(f"❌ Error loading Key Metrics Cash Flow for {ticker_value}: {e}")

                # KEY METRICS GROWTH
                try:
                    valuation_growth_data = database.child('valuation_growth').child(db_key_prefix).get().val()
                    if valuation_growth_data and valuation_growth_data != '{"valuation_growth":{"none":"no data"}}':
                        valuation_growth_data = json.loads(valuation_growth_data)
                        df6 = pd.DataFrame(valuation_growth_data)
                        dataframes['Key Metrics Growth'] = df6
                        print(f"✅ Key Metrics Growth data loaded for {ticker_value} ALL export")
                    else:
                        print(f"❌ No Key Metrics Growth data available for {ticker_value}")
                except Exception as e:
                    print(f"❌ Error loading Key Metrics Growth for {ticker_value}: {e}")

                # KEY METRICS FINANCIAL HEALTH
                try:
                    valuation_financial_health_data = database.child('valuation_financial_health').child(db_key_prefix).get().val()
                    if valuation_financial_health_data and valuation_financial_health_data != '{"valuation_financial_health":{"none":"no data"}}':
                        valuation_financial_health_data = json.loads(valuation_financial_health_data)
                        df7 = pd.DataFrame(valuation_financial_health_data)
                        dataframes['Key Metrics Financial Health'] = df7
                        print(f"✅ Key Metrics Financial Health data loaded for {ticker_value} ALL export")
                    else:
                        print(f"❌ No Key Metrics Financial Health data available for {ticker_value}")
                except Exception as e:
                    print(f"❌ Error loading Key Metrics Financial Health for {ticker_value}: {e}")

                # VALUATION
                try:
                    valuation_data = database.child('valuation').child(db_key_prefix).get().val()
                    if valuation_data and valuation_data != '{"valuation":{"none":"no data"}}':
                        valuation_data = json.loads(valuation_data)
                        df8 = pd.DataFrame(valuation_data)
                        dataframes['Valuation'] = df8
                        print(f"✅ Valuation data loaded for {ticker_value} ALL export")
                    else:
                        print(f"❌ No Valuation data available for {ticker_value}")
                except Exception as e:
                    print(f"❌ Error loading Valuation for {ticker_value}: {e}")

                # Create comprehensive Excel file with all available data
                if dataframes:
                    writer = pd.ExcelWriter("all_stock_data.xlsx", engine='xlsxwriter')
                    
                    # Write each dataframe to a separate sheet
                    for sheet_name, df in dataframes.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        print(f"✅ Added {sheet_name} to Excel file")
                    
                    writer.close()
                    
                    # Return the Excel file
                    with open("all_stock_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                        response['Content-Disposition'] = 'attachment; filename=all_stock_data.xlsx'   
                        return response
                else:
                    # No data available, create a simple message file
                    df_no_data = pd.DataFrame({"Message": ["No data available for any categories"]})
                    writer = pd.ExcelWriter("no_data.xlsx", engine='xlsxwriter')
                    df_no_data.to_excel(writer, sheet_name='No Data', index=False)
                    writer.close()
                    
                    with open("no_data.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                        response['Content-Disposition'] = 'attachment; filename=no_data_available.xlsx'   
                        return response
                        
            except Exception as e:
                print(f"❌ Error creating ALL Excel file: {e}")
                # Return error message as Excel file
                df_error = pd.DataFrame({"Error": [f"Error creating comprehensive file: {str(e)}"]})
                writer = pd.ExcelWriter("error.xlsx", engine='xlsxwriter')
                df_error.to_excel(writer, sheet_name='Error', index=False)
                writer.close()
                
                with open("error.xlsx", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = 'attachment; filename=error.xlsx'   
                    return response
        else:
             return render(request, "../templates/loadScreen.html")


    else:
        return render(request, "../templates/stockData.html")


def financial_statements_json(request):
    """
    API endpoint to return financial statements data in JSON format
    """
    if request.method == 'GET':
        # Get parameters from URL
        ticker_value = request.GET.get('ticker', '').upper()
        market_value = request.GET.get('market', '').upper()
        
        if not ticker_value or not market_value:
            return JsonResponse({
                'error': 'Missing required parameters: ticker and market'
            }, status=400)
        
        # Create ticker-specific database key
        db_key_prefix = f"{ticker_value}_{market_value}"
        
        try:
            # Fetch data from Firebase using ticker-specific keys
            income_statement_data = database.child('income_statement').child(db_key_prefix).get().val()
            balance_sheet_data = database.child('balance_sheet').child(db_key_prefix).get().val()
            cash_flow_data = database.child('cash_flow').child(db_key_prefix).get().val()
            
            # Parse JSON data
            income_statement = None
            balance_sheet = None
            cash_flow = None
            
            if income_statement_data:
                try:
                    income_statement = json.loads(income_statement_data)
                except json.JSONDecodeError:
                    income_statement = {"error": "Invalid JSON data"}
            
            if balance_sheet_data:
                try:
                    balance_sheet = json.loads(balance_sheet_data)
                except json.JSONDecodeError:
                    balance_sheet = {"error": "Invalid JSON data"}
            
            if cash_flow_data:
                try:
                    cash_flow = json.loads(cash_flow_data)
                except json.JSONDecodeError:
                    cash_flow = {"error": "Invalid JSON data"}
            
            # Return combined data
            response_data = {
                'ticker': ticker_value,
                'market': market_value,
                'data': {
                    'income_statement': income_statement,
                    'balance_sheet': balance_sheet,
                    'cash_flow': cash_flow
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'error': f'Failed to fetch data: {str(e)}',
                'ticker': ticker_value,
                'market': market_value
            }, status=500)
    
    else:
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)



