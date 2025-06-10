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


from core.views import get_balance_sheet
from requests.structures import CaseInsensitiveDict
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.shortcuts import render,redirect
import requests
import json 
from typing import List, final
from collections.abc import Iterable
from django.http import HttpResponse
import re
from bs4 import BeautifulSoup
import csv
import pandas as pd
from json import loads
import requests
from time import *
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

def scrape(request):
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
        # elif download_type == "OPERATING_PERFORMANCE":
        #     task = scraper_operating_performance.delay(ticker_value=ticker_value, market_value=market_value)
        #     return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type == "ALL":
            task = all_scraper.delay(ticker_value=ticker_value, market_value=market_value)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        else:
            return render(request, "../templates/stockData.html")
    elif 'download' in request.POST:
        if download_type == "INCOME_STATEMENT": 
            income_statement_data = database.child('income_statement').child('income_statement').get().val()
            income_statement_data = json.loads(income_statement_data)
            new_dict = remove_whitespaces(income_statement_data)
            df = pd.DataFrame(new_dict).to_excel("income_statement.xlsx", index=False)
            with open("income_statement.xlsx", 'rb') as file:
                response = HttpResponse(file, content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                return response
        elif download_type == "BALANCE_SHEET":
            balance_sheet_data = database.child('balance_sheet').child('balance_sheet').get().val()
            balance_sheet_data = json.loads(balance_sheet_data)
            new_dict = remove_whitespaces(balance_sheet_data)  
            df = pd.DataFrame(new_dict).to_excel("balance_sheet.xlsx", index=False)
            with open("balance_sheet.xlsx", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'  
                    return response
        elif download_type == "CASH_FLOW":
                cash_flow_data = database.child('cash_flow').child('cash_flow').get().val()
                cash_flow_data = json.loads(cash_flow_data)
                new_dict = remove_whitespaces(cash_flow_data)  
                df = pd.DataFrame(new_dict).to_excel("cash_flow.xlsx", index=False)
                with open("cash_flow.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                        return response
        elif download_type == "DIVIDENDS":
            dividends_data = database.child('dividends').child('dividends').get().val()
            dividends_data = json.loads(dividends_data)
            print(dividends_data)
            df = pd.DataFrame(dividends_data).to_excel("dividends_data.xlsx", index=False)
            with open("dividends_data.xlsx", 'rb') as file:
                response = HttpResponse(file, content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                return response
        elif download_type == "OPERATING_PERFORMANCE":
                operating_performance_data = database.child('operating_performance').child('operating_performance').get().val()
                operating_performance_data = json.loads(operating_performance_data)
                print(operating_performance_data)
                df = pd.DataFrame(operating_performance_data).to_excel("operating_performance.xlsx", index=False)
                with open("operating_performance.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                        return response
        elif download_type == "KEY_METRICS_CASH_FLOW":
                valuation_cash_flow_data = database.child('valuation_cash_flow').child('valuation_cash_flow').get().val()
                valuation_cash_flow_data = json.loads(valuation_cash_flow_data)
                print(valuation_cash_flow_data)
                df = pd.DataFrame(valuation_cash_flow_data).to_excel("valuation_cash_flow.xlsx", index=False)
                with open("valuation_cash_flow.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                        return response
        elif download_type == "KEY_METRICS_GROWTH":
                valuation_growth_data = database.child('valuation_growth').child('valuation_growth').get().val()
                valuation_growth_data = json.loads(valuation_growth_data)
                print(valuation_growth_data)
                df = pd.DataFrame(valuation_growth_data).to_excel("valuation_growth.xlsx", index=False)
                with open("valuation_growth.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                        return response
        elif download_type == "KEY_METRICS_FINANCIAL_HEALTH":
                valuation_financial_health_data = database.child('valuation_financial_health').child('valuation_financial_health').get().val()
                valuation_financial_health_data = json.loads(valuation_financial_health_data)
                print(valuation_financial_health_data)
                df = pd.DataFrame(valuation_financial_health_data).to_excel("valuation_financial_health.xlsx", index=False)
                with open("valuation_financial_health.xlsx", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                    return response
        elif download_type == "VALUATION_OPERATING_EFFICIENCY":
                valuation_operating_efficiency_data = database.child('valuation_operating_efficiency').child('valuation_operating_efficiency').get().val()
                valuation_operating_efficiency_data = json.loads(valuation_operating_efficiency_data)
                print(valuation_operating_efficiency_data)
                df = pd.DataFrame(valuation_operating_efficiency_data).to_excel("valuation_operating_efficiency.xlsx", index=False)
                with open("valuation_operating_efficiency.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                        return response
        elif download_type == "ALL":
            # Create comprehensive Excel file with all scraped data
            dataframes = {}
            
            try:
                # INCOME STATEMENT
                try:
                    income_statement_data = database.child('income_statement').child('income_statement').get().val()
                    if income_statement_data and income_statement_data != '{"income_statement":{"none":"no data"}}':
                        income_statement_data = json.loads(income_statement_data)
                        new_dict = remove_whitespaces(income_statement_data)  
                        df1 = pd.DataFrame(new_dict)
                        dataframes['Income Statement'] = df1
                        print("✅ Income Statement data loaded for ALL export")
                    else:
                        print("❌ No Income Statement data available")
                except Exception as e:
                    print(f"❌ Error loading Income Statement: {e}")
                
                # BALANCE SHEET
                try:
                    balance_sheet_data = database.child('balance_sheet').child('balance_sheet').get().val()
                    if balance_sheet_data and balance_sheet_data != '{"balance_sheet":{"none":"no data"}}':
                        balance_sheet_data = json.loads(balance_sheet_data)
                        new_dict = remove_whitespaces(balance_sheet_data)  
                        df2 = pd.DataFrame(new_dict)
                        dataframes['Balance Sheet'] = df2
                        print("✅ Balance Sheet data loaded for ALL export")
                    else:
                        print("❌ No Balance Sheet data available")
                except Exception as e:
                    print(f"❌ Error loading Balance Sheet: {e}")
                
                # CASH FLOW
                try:
                    cash_flow_data = database.child('cash_flow').child('cash_flow').get().val()
                    if cash_flow_data and cash_flow_data != '{"cash_flow":{"none":"no data"}}':
                        cash_flow_data = json.loads(cash_flow_data)
                        new_dict = remove_whitespaces(cash_flow_data)  
                        df3 = pd.DataFrame(new_dict)
                        dataframes['Cash Flow'] = df3
                        print("✅ Cash Flow data loaded for ALL export")
                    else:
                        print("❌ No Cash Flow data available")
                except Exception as e:
                    print(f"❌ Error loading Cash Flow: {e}")
                
                # DIVIDENDS
                try:
                    dividends_data = database.child('dividends').child('dividends').get().val()
                    if dividends_data and dividends_data != '{"dividends":{"none":"no data"}}':
                        dividends_data = json.loads(dividends_data)
                        df4 = pd.DataFrame(dividends_data)
                        dataframes['Dividends'] = df4
                        print("✅ Dividends data loaded for ALL export")
                    else:
                        print("❌ No Dividends data available")
                except Exception as e:
                    print(f"❌ Error loading Dividends: {e}")

                # KEY METRICS CASH FLOW
                try:
                    valuation_cash_flow_data = database.child('valuation_cash_flow').child('valuation_cash_flow').get().val()
                    if valuation_cash_flow_data and valuation_cash_flow_data != '{"valuation_cash_flow":{"none":"no data"}}':
                        valuation_cash_flow_data = json.loads(valuation_cash_flow_data)
                        df5 = pd.DataFrame(valuation_cash_flow_data)
                        dataframes['Key Metrics Cash Flow'] = df5
                        print("✅ Key Metrics Cash Flow data loaded for ALL export")
                    else:
                        print("❌ No Key Metrics Cash Flow data available")
                except Exception as e:
                    print(f"❌ Error loading Key Metrics Cash Flow: {e}")

                # KEY METRICS GROWTH
                try:
                    valuation_growth_data = database.child('valuation_growth').child('valuation_growth').get().val()
                    if valuation_growth_data and valuation_growth_data != '{"valuation_growth":{"none":"no data"}}':
                        valuation_growth_data = json.loads(valuation_growth_data)
                        df6 = pd.DataFrame(valuation_growth_data)
                        dataframes['Key Metrics Growth'] = df6
                        print("✅ Key Metrics Growth data loaded for ALL export")
                    else:
                        print("❌ No Key Metrics Growth data available")
                except Exception as e:
                    print(f"❌ Error loading Key Metrics Growth: {e}")

                # KEY METRICS FINANCIAL HEALTH
                try:
                    valuation_financial_health_data = database.child('valuation_financial_health').child('valuation_financial_health').get().val()
                    if valuation_financial_health_data and valuation_financial_health_data != '{"valuation_financial_health":{"none":"no data"}}':
                        valuation_financial_health_data = json.loads(valuation_financial_health_data)
                        df7 = pd.DataFrame(valuation_financial_health_data)
                        dataframes['Key Metrics Financial Health'] = df7
                        print("✅ Key Metrics Financial Health data loaded for ALL export")
                    else:
                        print("❌ No Key Metrics Financial Health data available")
                except Exception as e:
                    print(f"❌ Error loading Key Metrics Financial Health: {e}")

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



