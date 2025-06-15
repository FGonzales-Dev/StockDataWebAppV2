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
            task = AsyncResult(task_id)
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
                
            return JsonResponse(data)
        except Exception as e:
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
        elif download_type == "VALUATION_CASH_FLOW" or download_type == "VALUATION_GROWTH" or download_type == "VALUATION_FINANCIAL_HEALTH" or download_type == "VALUATION_OPERATING_EFFICIENCY":
            task = scraper_valuation.delay(ticker_value=ticker_value, market_value=market_value, download_type=download_type)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type =="DIVIDENDS":
            task = scraper_dividends.delay(ticker_value=ticker_value, market_value=market_value)
            dividends_task_id = task.id
            print(dividends_task_id)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type == "OPERATING_PERFORMANCE":
            task = scraper_operating_performance.delay(ticker_value=ticker_value, market_value=market_value)
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
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
        elif download_type == "VALUATION_CASH_FLOW":
                valuation_cash_flow_data = database.child('valuation_cash_flow').child('valuation_cash_flow').get().val()
                valuation_cash_flow_data = json.loads(valuation_cash_flow_data)
                print(valuation_cash_flow_data)
                df = pd.DataFrame(valuation_cash_flow_data).to_excel("valuation_cash_flow.xlsx", index=False)
                with open("valuation_cash_flow.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                        return response
        elif download_type == "VALUATION_GROWTH":
                valuation_growth_data = database.child('valuation_growth').child('valuation_growth').get().val()
                valuation_growth_data = json.loads(valuation_growth_data)
                print(valuation_growth_data)
                df = pd.DataFrame(valuation_growth_data).to_excel("valuation_growth.xlsx", index=False)
                with open("valuation_growth.xlsx", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xlsx'   
                        return response
        elif download_type == "VALUATION_FINANCIAL_HEALTH":
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
            #INCOME STATEMENT
            income_statement_data = database.child('income_statement').child('income_statement').get().val()
            income_statement_data = json.loads(income_statement_data)
            new_dict = remove_whitespaces(income_statement_data)  
            df1 = pd.DataFrame(new_dict).to_excel("income_statement.xlsx", index=False)
            df1 = pd.read_excel('income_statement.xlsx')
            #BALANCE SHEET
            balance_sheet_data = database.child('balance_sheet').child('balance_sheet').get().val()
            balance_sheet_data = json.loads(balance_sheet_data)
            new_dict = remove_whitespaces(balance_sheet_data)  
            df2 = pd.DataFrame(new_dict).to_excel("balance_sheet.xlsx", index=False)
            df2 = pd.read_excel('balance_sheet.xlsx')
            #CASH FLOW
            cash_flow_data = database.child('cash_flow').child('cash_flow').get().val()
            cash_flow_data = json.loads(cash_flow_data)
            new_dict = remove_whitespaces(cash_flow_data)  
            df3 = pd.DataFrame(new_dict).to_excel("cash_flow.xlsx", index=False)
            df3 = pd.read_excel('cash_flow.xlsx')
          

            #DIVIDENDS
            dividends_data = database.child('dividends').child('dividends').get().val()
            dividends_data = json.loads(dividends_data)
            print(dividends_data)
            df4 = pd.DataFrame(dividends_data).to_excel("dividends_data.xlsx", index=False)
            df4 = pd.read_excel('dividends_data.xlsx')

            #VALUATION CASH FLOW
            valuation_cash_flow_data = database.child('valuation_cash_flow').child('valuation_cash_flow').get().val()
            valuation_cash_flow_data = json.loads(valuation_cash_flow_data)
            print(valuation_cash_flow_data)
            d5 = pd.DataFrame(valuation_cash_flow_data).to_excel("valuation_cash_flow.xlsx", index=False)
            df5 = pd.read_excel('valuation_cash_flow.xlsx')

            #VALUATION GROWTH
            valuation_growth_data = database.child('valuation_growth').child('valuation_growth').get().val()
            valuation_growth_data = json.loads(valuation_growth_data)
            print(valuation_growth_data)
            df6 = pd.DataFrame(valuation_growth_data).to_excel("valuation_growth.xlsx", index=False)
            df6 = pd.read_excel('valuation_growth.xlsx')

            #VALUATION FINANCIAL HEALTH
            valuation_financial_health_data = database.child('valuation_financial_health').child('valuation_financial_health').get().val()
            valuation_financial_health_data = json.loads(valuation_financial_health_data)
            print(valuation_financial_health_data)
            df7 = pd.DataFrame(valuation_financial_health_data).to_excel("valuation_financial_health.xlsx", index=False)
            df7 = pd.read_excel('valuation_financial_health.xlsx')

            #VALUATION OPERATING EFFICIENCY
            valuation_operating_efficiency_data = database.child('valuation_operating_efficiency').child('valuation_operating_efficiency').get().val()
            valuation_operating_efficiency_data = json.loads(valuation_operating_efficiency_data)
            print(valuation_operating_efficiency_data)
            df8 = pd.DataFrame(valuation_operating_efficiency_data).to_excel("valuation_operating_efficiency.xlsx", index=False)
            df8 = pd.read_excel('valuation_operating_efficiency.xlsx')


           
           # OPERATING PERFORMANCE
            operating_performance_data = database.child('operating_performance').child('operating_performance').get().val()
            operating_performance_data = json.loads(operating_performance_data)
            print(operating_performance_data)
            df9 = pd.DataFrame(operating_performance_data).to_excel("operating_performance.xlsx", index=False)
            df9 = pd.read_excel('operating_performance.xlsx')

            #ALL excel sheet generator        
            writer = pd.ExcelWriter("all.xls", engine = 'xlsxwriter')
            df1.to_excel(writer, sheet_name = 'Income Statement', index=False)
            df2.to_excel(writer, sheet_name = 'Balance Sheet', index=False)
            df3.to_excel(writer, sheet_name = 'Cash Flow', index=False)
            df4.to_excel(writer, sheet_name = 'Dividends', index=False)
            df5.to_excel(writer, sheet_name = 'Valuation Cash Flow', index=False)
            df6.to_excel(writer, sheet_name = 'Valuation Growth', index=False)
            df7.to_excel(writer, sheet_name = 'Valuation Financial Health', index=False)
            df8.to_excel(writer, sheet_name = 'Valuation Operating Efficiency', index=False)
            df9.to_excel(writer,sheet_name="Operating Performance", index=False)
            writer.save()
            writer.close()
            
            with open("all.xls", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
                    return response
        else:
             return render(request, "../templates/loadScreen.html")


    else:
        return render(request, "../templates/stockData.html")



