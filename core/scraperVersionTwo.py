
from operator import index
import os
from zlib import DEF_BUF_SIZE
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from django.http import HttpResponseRedirect
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from cb_dj_weather_app.settings import BASE_DIR, STATIC_ROOT
import shutil
from webdriver_manager.chrome import ChromeDriverManager
from django.http import FileResponse
from pathlib import Path
import string

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
from collections import Iterable
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
from celery.result import AsyncResult


def get_task_info(request):
    task_id = request.GET.get('task_id', None)
    if task_id is not None:
        task = AsyncResult(task_id)
        data = {
            'state': task.state,
            'result': task.result,
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponse('No job id given.')


def download(request):
    return render(request, "../templates/loadScreen.html")




def scrape(request):
    
    ticker_value =  request.POST.get("ticker", "")
    market_value =  request.POST.get("market", "")
    download_type = request.POST.get("download_type", "")
    task_id = request.POST.get("task_id", "")
   
    if 'get_data' in request.POST:
        print("============================")
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
           
            # dividends_json = json.loads(task.get())
            # dividends_json.to_json ('dividends.json', orient='records')
            # a_file = open("dividends.json", "r")
            # a_file.close()
            # pd.read_json("dividends.json").to_excel('dividends.xls',index=False)
           
            # return HttpResponse(task, content_type='text/json')
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type == "OPERATING_PERFORMANCE":
            task =scraper_operating_performance.delay(ticker_value=ticker_value, market_value=market_value)
          
            return render(request, "../templates/loadScreen.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        elif download_type == "ALL":
            scraper.delay(ticker_value=ticker_value, market_value=market_value, download_type="INCOME_STATEMENT")
            scraper.delay(ticker_value=ticker_value, market_value=market_value, download_type="BALANCE_SHEET")
            scraper.delay(ticker_value=ticker_value, market_value=market_value, download_type="CASH_FLOW")
            scraper_valuation.delay(ticker_value=ticker_value, market_value=market_value, download_type="VALUATION_CASH_FLOW")
            scraper_valuation.delay(ticker_value=ticker_value, market_value=market_value, download_type="VALUATION_GROWTH")
            scraper_valuation.delay(ticker_value=ticker_value, market_value=market_value, download_type="VALUATION_FINANCIAL_HEALTH")
            scraper_valuation.delay(ticker_value=ticker_value, market_value=market_value, download_type="VALUATION_OPERATING_EFFICIENCY")
            scraper_operating_performance.delay(ticker_value=ticker_value, market_value=market_value)
            task = scraper_dividends.delay(ticker_value=ticker_value, market_value=market_value)
            return render(request, "../templates/load_screen_all.html",{ "download_type": download_type,"task_id": task.id, "task_stat": task.status})
        else:
            return render(request, "../templates/stockData.html")
    elif 'download' in request.POST:
        if download_type == "INCOME_STATEMENT": 
            data_xls = pd.read_excel(BASE_DIR + "/selenium/Income Statement_Annual_As Originally Reported.xls")
            data_xls.to_json('income_statement_test.json')
            with open('income_statement_test.json', 'r') as file:
                        content = file.read()
                        clean = content.replace(' ','')  # cleanup here
                        json_data = json.loads(clean)
                        file = json.dumps(json_data)
                        jsont = json.loads(file)
                        df = pd.DataFrame(data=jsont)
                        df.to_excel('income_statement.xls',index=False)
            with open("income_statement.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'  
                        return response
        elif download_type == "BALANCE_SHEET":
                data_xls = pd.read_excel(BASE_DIR + "/selenium/Balance Sheet_Annual_As Originally Reported.xls")
                data_xls.to_json('balance_sheet_test.json')
                with open('balance_sheet_test.json', 'r') as file:
                        content = file.read()
                        clean = content.replace(' ','')  # cleanup here
                        json_data = json.loads(clean)
                        file = json.dumps(json_data)
                        jsont = json.loads(file)
                        df = pd.DataFrame(data=jsont)
                        df.to_excel('balance_sheet.xls',index=False)       
                with open("balance_sheet.xls", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=stockData.xls'  
                    return response
        elif download_type == "CASH_FLOW":
                data_xls = pd.read_excel(BASE_DIR + "/selenium/Cash Flow_Annual_As Originally Reported.xls")
                data_xls.to_json('cash_flow_test.json')
                with open('cash_flow_test.json', 'r') as file:
                        content = file.read()
                        clean = content.replace(' ','')  # cleanup here
                        json_data = json.loads(clean)
                        file = json.dumps(json_data)
                        jsont = json.loads(file)
                        df = pd.DataFrame(data=jsont)
                        df.to_excel('cash_flow.xls',index=False)          
                with open("cash_flow.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
                        return response
        elif download_type == "DIVIDENDS":
            
            res = AsyncResult(task_id).get()
            df = pd.read_json(res)
            df.to_excel('dividends.xls', index=False)
            with open("dividends.xls", 'rb') as file:
                response = HttpResponse(file, content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
           
        elif download_type == "OPERATING_PERFORMANCE":
                with open("operating_performance.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
                        return response
        elif download_type == "VALUATION_CASH_FLOW":
                pd.read_excel("valuation_cash_flow.xls")
                with open("valuation_cash_flow.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
                        return response
        elif download_type == "VALUATION_GROWTH":
                pd.read_excel("valuation_growth.xls")
                with open("valuation_growth.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
                        return response
        elif download_type == "VALUATION_FINANCIAL_HEALTH":
                pd.read_excel("valuation_financial_health.xls")
                with open("valuation_financial_health.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
                        return response
        elif download_type == "VALUATION_OPERATING_EFFICIENCY":
                pd.read_excel("valuation_operating_efficiency.xls")
                with open("valuation_operating_efficiency.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
                        return response
        elif download_type == "ALL":
            data_xls = pd.read_excel(BASE_DIR + "/selenium/Balance Sheet_Annual_As Originally Reported.xls")
            data_xls.to_json('balance_sheet_test.json')
            with open('balance_sheet_test.json', 'r') as file:
                        content = file.read()
                        clean = content.replace(' ','')  # cleanup here
                        json_data = json.loads(clean)
                        file = json.dumps(json_data)
                        jsont = json.loads(file)
                        df = pd.DataFrame(data=jsont)
                        df.to_excel('balance_sheet.xls',index=False)
                        df1 = pd.read_excel('balance_sheet.xls')
            
            data_xls = pd.read_excel(BASE_DIR + "/selenium/Cash Flow_Annual_As Originally Reported.xls")
            data_xls.to_json('cash_flow_test.json')
            with open('cash_flow_test.json', 'r') as file:
                        content = file.read()
                        clean = content.replace(' ','')  # cleanup here
                        json_data = json.loads(clean)
                        file = json.dumps(json_data)
                        jsont = json.loads(file)
                        df = pd.DataFrame(data=jsont)
                        df.to_excel('cash_flow.xls',index=False)
                        df2 = pd.read_excel('cash_flow.xls')
            data_xls = pd.read_excel(BASE_DIR + "/selenium/Income Statement_Annual_As Originally Reported.xls")
            data_xls.to_json('income_statement_test.json')
            with open('income_statement_test.json', 'r') as file:
                        content = file.read()
                        clean = content.replace(' ','')  # cleanup here
                        json_data = json.loads(clean)
                        file = json.dumps(json_data)
                        jsont = json.loads(file)
                        df = pd.DataFrame(data=jsont)
                        df.to_excel('income_statement.xls',index=False)
                        df3 = pd.read_excel('income_statement.xls')
            df4 = pd.read_excel("dividends.xls")
            df5 = pd.read_excel("valuation_cash_flow.xls")
            df6 = pd.read_excel("valuation_growth.xls")
            df7 = pd.read_excel("valuation_financial_health.xls")
            df8 = pd.read_excel("valuation_operating_efficiency.xls")
            df9 = pd.read_excel("operating_performance.xls")
            
            writer = pd.ExcelWriter("all.xls", engine = 'xlsxwriter')
            df1.to_excel(writer, sheet_name = 'BALANCE SHEET', index=False)
            df2.to_excel(writer, sheet_name = 'CASH FLOW', index=False)
            df3.to_excel(writer, sheet_name = 'INCOME STATEMENT', index=False)
            df5.to_excel(writer, sheet_name = 'VALUATION CASH FLOW', index=False)
            df6.to_excel(writer, sheet_name = 'VALUATION GROWTH', index=False)
            df7.to_excel(writer, sheet_name = 'VALUATION FINANCIAL HEALTH', index=False)
            df8.to_excel(writer, sheet_name = 'VALUATION OPERATING EFFICIENCY', index=False)
            df4.to_excel(writer, sheet_name = 'DIVIDENDS', index=False)
            df9.to_excel(writer,sheet_name="OPERATING PERFORMANCE", index=False)
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
