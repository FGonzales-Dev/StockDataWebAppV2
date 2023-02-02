
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
            CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
            prefs = {'download.default_directory' :  BASE_DIR}
            chromeOptions = webdriver.ChromeOptions()
            chromeOptions.add_experimental_option('prefs', prefs)
            chromeOptions.add_argument('--headless')
            chromeOptions.add_argument('--disable-setuid-sandbox')
            chromeOptions.add_argument('--remote-debugging-port=9222')
            chromeOptions.add_argument('--disable-extensions')
            chromeOptions.add_argument('start-maximized')
            chromeOptions.add_argument('--disable-gpu')
            chromeOptions.add_argument('--no-sandbox')
            chromeOptions.add_argument('--disable-dev-shm-usage')
            # driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chromeOptions)
            driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)
            driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Income Statement')]"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
            sleep(5)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Balance Sheet')]"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
            sleep(5)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
            sleep(5)
            driver.quit()
            # scraper_operating_performance.delay(ticker_value=ticker_value, market_value=market_value)
            scraper_dividends.delay(ticker_value=ticker_value, market_value=market_value)
            return render(request, "../templates/load_screen_all.html",{ "download_type": download_type})
        else:
            return render(request, "../templates/stockData.html")
    elif 'download' in request.POST:
        if download_type == "INCOME_STATEMENT": 
            storage.child("income_statement.xls").download(BASE_DIR, filename="income_statement.xls")
            
            with open("income_statement.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'  
                        return response
        elif download_type == "BALANCE_SHEET":
                storage.child("balance_sheet.xls").download(BASE_DIR, filename="balance_sheet.xls")    
                with open("balance_sheet.xls", 'rb') as file:
                    response = HttpResponse(file, content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=stockData.xls'  
                    return response
        elif download_type == "CASH_FLOW":
                storage.child("cash_flow.xls").download(BASE_DIR, filename="cash_flow.xls")
                with open("cash_flow.xls", 'rb') as file:
                        response = HttpResponse(file, content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=stockData.xls'   
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
            data_xls = pd.read_excel(BASE_DIR + "/Balance Sheet_Annual_As Originally Reported.xls")
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
            data_xls = pd.read_excel(BASE_DIR + "/Cash Flow_Annual_As Originally Reported.xls")
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
            data_xls = pd.read_excel(BASE_DIR + "/Income Statement_Annual_As Originally Reported.xls")
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
            


            #DIVIDENDS
            dividends_data = database.child('dividends').child('dividends').get().val()
            dividends_data = json.loads(dividends_data)
            print(dividends_data)
            df4 = pd.DataFrame(dividends_data).to_excel("dividends_data.xlsx", index=False)
            df4 = pd.read_excel('dividends_data.xls')
           
           # OPERATING PERFORMANCE
            operating_performance_data = database.child('operating_performance').child('operating_performance').get().val()
            operating_performance_data = json.loads(operating_performance_data)
            print(operating_performance_data)
            df9 = pd.DataFrame(operating_performance_data).to_excel("operating_performance.xlsx", index=False)
            df9 = pd.read_excel('operating_performance.xls')
            

            # df6 = pd.read_excel("valuation_growth.xls", index_col=0)
            # df7 = pd.read_excel("valuation_financial_health.xls", index_col=0)
            # df8 = pd.read_excel("valuation_operating_efficiency.xls", index_col=0)
            # df9 = pd.read_excel("operating_performance.xls", index_col=0)
            
            writer = pd.ExcelWriter("all.xls", engine = 'xlsxwriter')
            df1.to_excel(writer, sheet_name = 'Balance Sheet', index=False)
            df2.to_excel(writer, sheet_name = 'Cash Flow', index=False)
            df3.to_excel(writer, sheet_name = 'Income Statement', index=False)
            # df5.to_excel(writer, sheet_name = 'Valuation Cash Flow', index=False)
            # df6.to_excel(writer, sheet_name = 'Valuation Growth', index=False)
            # df7.to_excel(writer, sheet_name = 'Valuation Financial Health', index=False)
            # df8.to_excel(writer, sheet_name = 'Valuation Operating Efficiency', index=False)
            # df4.to_excel(writer, sheet_name = 'Dividends', index=False)
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



