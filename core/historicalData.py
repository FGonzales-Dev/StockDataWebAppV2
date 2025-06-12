##### TO BE DEPRECATED #####


# import email
# import os
# from selenium import webdriver
# from selenium.webdriver.support import expected_conditions as EC
# from datetime import datetime
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.by import By
# from stock_scraper.settings import BASE_DIR, STATIC_ROOT
# import shutil
# from webdriver_manager.chrome import ChromeDriverManager
# from django.http import FileResponse
# from pathlib import Path

# from time import sleep
# from email import header
# import profile

# from core.views import get_balance_sheet
# from requests.structures import CaseInsensitiveDict
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from django.shortcuts import render
# import requests
# import json 
# from typing import List, final
# from collections.abc import Iterable
# from django.http import HttpResponse
# import re
# from bs4 import BeautifulSoup
# import csv
# import pandas as pd
# from json import loads
# import requests
# from time import *
# from time import sleep
# import glob
# from django.http import JsonResponse

# from .models import APIRequest
# from register.models import Profile
# from django.contrib.auth.models import User


# # Import scraper configuration
# try:
#     from scraper_config import *
# except ImportError:
#     # Fallback defaults if config file doesn't exist
#     SHOW_BROWSER = False
#     DEBUG_MODE = False
#     SAVE_DEBUG_SCREENSHOTS = False
#     SAVE_DEBUG_PAGE_SOURCE = False
#     ELEMENT_WAIT_TIMEOUT = 30
#     PAGE_LOAD_TIMEOUT = 60
#     BROWSER_WIDTH = 1920
#     BROWSER_HEIGHT = 1080
#     USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
#     DOWNLOAD_DIRECTORY = "/selenium"

# def get_chrome_driver(chrome_options=None):
#     """
#     Create Chrome WebDriver with automatic environment detection.
#     Uses CHROMEDRIVER_PATH environment variable for production,
#     local chromedriver path for development, with WebDriverManager as fallback.
#     """
#     CHROME_DRIVER_PATH = BASE_DIR + "/chromedriver"
    
#     # Create chrome options if not provided
#     if chrome_options is None:
#         chrome_options = webdriver.ChromeOptions()
        
#         # Download preferences
#         prefs = {'download.default_directory': BASE_DIR + DOWNLOAD_DIRECTORY}
#         chrome_options.add_experimental_option('prefs', prefs)
        
#         # Basic options
#         chrome_options.add_argument("--disable-infobars")
#         chrome_options.add_argument("--disable-extensions")
#         chrome_options.add_argument('--no-sandbox')
#         chrome_options.add_argument("--disable-dev-shm-usage")
        
#         # Window size
#         chrome_options.add_argument(f"--window-size={BROWSER_WIDTH},{BROWSER_HEIGHT}")
        
#         # User agent
#         chrome_options.add_argument(f"user-agent={USER_AGENT}")
        
#         # Headless mode based on configuration
#         if not SHOW_BROWSER:
#             chrome_options.add_argument("--headless")
#             print("🔍 Running in HEADLESS mode (browser hidden)")
#         else:
#             chrome_options.add_argument("--start-maximized")
#             print("👁️ Running in VISIBLE mode (browser will be shown)")
    
#     if os.environ.get("CHROMEDRIVER_PATH"):
#         # Production environment (Heroku, etc.)
#         return webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
#     elif os.path.exists(CHROME_DRIVER_PATH):
#         # Local development environment with local chromedriver
#         return webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chrome_options)
#     else:
#         # Fallback: Use WebDriverManager to auto-download compatible ChromeDriver
#         return webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=chrome_options)

# def scrape_operating_performance(request):
#     if 'ticker' in request.GET and 'market' in request.GET:
#         ticker_value = request.GET.get("ticker", "")
#         market_value = request.GET.get("market", "")
#         CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
#         prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
#         chromeOptions = webdriver.ChromeOptions()
#         chromeOptions.add_experimental_option('prefs', prefs)
#         chromeOptions.add_argument("--disable-infobars")
#         chromeOptions.add_argument("--start-maximized")
#         chromeOptions.add_argument("--disable-extensions")
#         chromeOptions.add_argument('--window-size=1920,1080')
#         chromeOptions.add_argument('--no-sandbox')   
#         chromeOptions.add_argument("--disable-dev-shm-usage") 
        
#         # Create Chrome driver with automatic environment detection
#         driver = get_chrome_driver(chromeOptions)
#         driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/performance")
      
#         data = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
#         df  = pd.read_html(data)    
#         df[0].to_json ('jsonfile.json', orient='records')
#         a_file = open("jsonfile.json", "r")
#         a_json = json.load(a_file)
#         pretty_json = json.dumps(a_json).replace("null", '"0"')
#         a_file.close()
#         return HttpResponse(pretty_json, content_type='text/json')

# def scrape_dividends(request):
#     if 'ticker' in request.GET and 'market' in request.GET:
#         ticker_value = request.GET.get("ticker", "")
#         market_value = request.GET.get("market", "")
#         CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
#         prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
#         chromeOptions = webdriver.ChromeOptions()
#         chromeOptions.add_experimental_option('prefs', prefs)
#         chromeOptions.add_argument("--disable-infobars")
#         chromeOptions.add_argument("--start-maximized")
#         chromeOptions.add_argument("--disable-extensions")
#         chromeOptions.add_argument('--window-size=1920,1080')
#         chromeOptions.add_argument('--no-sandbox')   
#         chromeOptions.add_argument("--disable-dev-shm-usage") 
        
#         # Create Chrome driver with automatic environment detection
#         driver = get_chrome_driver(chromeOptions)
#         driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/dividends")
      
#         data = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
#         df  = pd.read_html(data)    
#         df[0].to_json ('jsonfile.json', orient='records')
#         a_file = open("jsonfile.json", "r")
#         a_json = json.load(a_file)
#         pretty_json = json.dumps(a_json).replace("null", '"0"')
#         a_file.close()
#         return HttpResponse(pretty_json, content_type='text/json')


# def scrape_valuation(request):
#     if 'ticker' in request.GET and 'market' in request.GET and 'type' in request.GET:
#         type_value = request.GET.get("type", "")
#         ticker_value = request.GET.get("ticker", "")
#         market_value = request.GET.get("market", "")
#         CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
#         prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
#         chromeOptions = webdriver.ChromeOptions()
#         chromeOptions.add_experimental_option('prefs', prefs)
#         chromeOptions.add_argument("--disable-infobars")
#         chromeOptions.add_argument("--start-maximized")
#         chromeOptions.add_argument("--disable-extensions")
#         chromeOptions.add_argument('--window-size=1920,1080')
#         chromeOptions.add_argument('--no-sandbox')   
#         chromeOptions.add_argument("--disable-dev-shm-usage") 
        
#         # Create Chrome driver with automatic environment detection
#         driver = get_chrome_driver(chromeOptions)
#         if type_value == "cf":
#             driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
#             data = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-cash-flow sal-eqcss-key-stats-cash-flow']"))).get_attribute("outerHTML")
#             df  = pd.read_html(data)    
#             df[0].to_json ('jsonfile.json', orient='records')
#             a_file = open("jsonfile.json", "r")
#             a_json = json.load(a_file)
#             pretty_json = json.dumps(a_json).replace("null", '"0"')
#             a_file.close()
#             return HttpResponse(pretty_json, content_type='text/json')

#         elif type_value == "fh":
#             driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Financial Health')]"))).click()
#             data = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-financial-health sal-eqcss-key-stats-financial-health']"))).get_attribute("outerHTML")
#             df  = pd.read_html(data)    
#             df[0].to_json ('jsonfile.json', orient='records')
#             a_file = open("jsonfile.json", "r")
#             a_json = json.load(a_file)
#             pretty_json = json.dumps(a_json).replace("null", '"0"')
#             a_file.close()
#             return HttpResponse(pretty_json, content_type='text/json')
#         elif type_value == "g":
#             driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Growth')]"))).click()
#             data = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-growth-table sal-eqcss-key-stats-growth-table']"))).get_attribute("outerHTML")
#             df  = pd.read_html(data)    
#             df[0].to_json ('jsonfile.json', orient='records')
#             a_file = open("jsonfile.json", "r")
#             a_json = json.load(a_file)
#             pretty_json = json.dumps(a_json).replace("null", '"0"')
#             a_file.close()
#             return HttpResponse(pretty_json, content_type='text/json')
#         elif type_value == "ef":
#             driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Operating and Efficiency')]"))).click()
#             data = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-oper-efficiency sal-eqcss-key-stats-oper-efficiency']"))).get_attribute("outerHTML")
#             df  = pd.read_html(data)    
#             df[0].to_json ('jsonfile.json', orient='records')
#             a_file = open("jsonfile.json", "r")
#             a_json = json.load(a_file)
#             pretty_json = json.dumps(a_json).replace("null", '"0"')
#             a_file.close()
#             return HttpResponse(pretty_json, content_type='text/json')
#         else: 
#             return HttpResponse('error', content_type='text/json')



# def scrape(request):
#     if 'ticker' in request.GET and 'market' in request.GET and 'type' in request.GET:
#         ticker_value = request.GET.get("ticker", "")
#         market_value = request.GET.get("market", "")
#         type_value = request.GET.get("type", "")
#         CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
#         prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
#         chromeOptions = webdriver.ChromeOptions()
#         chromeOptions.add_experimental_option('prefs', prefs)
#         chromeOptions.add_argument("--disable-infobars")
#         chromeOptions.add_argument("--start-maximized")
#         chromeOptions.add_argument("--disable-extensions")
#         chromeOptions.add_argument('--window-size=1920,1080')
#         chromeOptions.add_argument('--no-sandbox')   
#         chromeOptions.add_argument("--disable-dev-shm-usage") 
        
#         # Create Chrome driver with automatic environment detection
#         driver = get_chrome_driver(chromeOptions)
#         driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
#         if type_value == "is":
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
#             sleep(5)
#             driver.quit()
#             with open(BASE_DIR + "/selenium/Income Statement_Annual_As Originally Reported.xls", 'rb') as file:
#                 df = pd.read_excel (BASE_DIR + "/selenium/Income Statement_Annual_As Originally Reported.xls")
#                 df.replace(',','', regex=True, inplace=True)
#                 df.to_json ('jsonfile.json', orient='records')
#                 a_file = open("jsonfile.json", "r")
#                 a_json = json.load(a_file)
#                 pretty_json = json.dumps(a_json).replace("null", '"0"').replace(" ","")
#                 a_file.close()
#             return HttpResponse(pretty_json, content_type='text/json')
#         elif type_value == "bs":
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Balance Sheet')]"))).click()
#             # WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
#             # Click the export button using multiple possible selectors
#             try:
#                 # Try by ID first (most specific)
#                 WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "salEqsvFinancialsPopoverExport"))).click()
#             except:
#                 try:
#                     # Try by aria-label
#                     WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Export']"))).click()
#                 except:
#                     try:
#                         # Try by class and icon combination
#                         WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'mds-button--icon-only__sal') and .//span[@data-mds-icon-name='share']]"))).click()
#                     except:
#                         try:
#                             # Try by the export section container
#                             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'sal-financials__exportSection')]//button"))).click()
#                         except:
#                             # Fallback to the original selector
#                             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
#             sleep(5)
#             driver.quit()
#             with open(BASE_DIR + "/selenium/Balance Sheet_Annual_As Originally Reported.xls", 'rb') as file:
#                 df = pd.read_excel (BASE_DIR + "/selenium/Balance Sheet_Annual_As Originally Reported.xls")
#                 df.replace(',','', regex=True, inplace=True)
#                 df.to_json ('jsonfile.json', orient='records')
#                 a_file = open("jsonfile.json", "r")
#                 a_json = json.load(a_file)
#                 pretty_json = json.dumps(a_json).replace("null", '"0"').replace(" ","")
#                 a_file.close()
#             return HttpResponse(pretty_json, content_type='text/json')
#         elif type_value == "cf":
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
#             WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
#             sleep(5)
#             driver.quit()
#         with open(BASE_DIR + "/selenium/Cash Flow_Annual_As Originally Reported.xls", 'rb') as file:
#             df = pd.read_excel (BASE_DIR + "/selenium/Cash Flow_Annual_As Originally Reported.xls")
#             df.replace(',','', regex=True, inplace=True)
#             df.to_json ('jsonfile.json', orient='records')
#             a_file = open("jsonfile.json", "r")
#             a_json = json.load(a_file)
#             pretty_json = json.dumps(a_json).replace("null", '"0"').replace(" ","")
#             a_file.close()
#             return HttpResponse(pretty_json, content_type='text/json')


# def get_key_ratio(ticker,market):
#     headers = {
#         'Referer': 'http://financials.morningstar.com/ratios/r.html?t=EXPE&region=usa&culture=en-US',
#         }
#     stockmarket = market.GET.get('market')
#     stockmarket = stockmarket.replace(" ", "+")
#     stockticker = ticker.GET.get('ticker')
#     stockticker = stockticker.replace(" ", "+")
#     screen = requests.get(f"http://financials.morningstar.com/finan/ajax/exportKR2CSV.html?&callback=?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&order=asc", headers=headers)
#     return screen


# def get_stock_history_v1(ticker,market ,type):
#     headers = {
#         'Referer': 'http://financials.morningstar.com/ratios/r.html?t=EXPE&region=usa&culture=en-US',
#         }
#     stockmarket = market.GET.get('market')
#     stockmarket = stockmarket.replace(" ", "+")
#     stockticker = ticker.GET.get('ticker')
#     stockticker = stockticker.replace(" ", "+")
#     stocktype = type.GET.get('type')
#     stocktype = stocktype.replace(" ", "+")
#     screen = requests.get(f"http://financials.morningstar.com/ajax/ReportProcess4CSV.html?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&reportType={stocktype}&period=12&dataType=A&order=asc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=13805&denominatorView=raw&number=3", headers=headers)
#     return screen

# def get_stock_balance_sheet(ticker,market):
#     headers = {
#         'Referer': 'http://financials.morningstar.com/ratios/r.html?t=EXPE&region=usa&culture=en-US',
#         }
#     stockmarket = market.GET.get('market')
#     stockmarket = stockmarket.replace(" ", "+")
#     stockticker = ticker.GET.get('ticker')
#     stockticker = stockticker.replace(" ", "+")
#     screen = requests.get(f"http://financials.morningstar.com/ajax/ReportProcess4CSV.html?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&reportType=bs&period=12&dataType=A&order=asc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=13805&denominatorView=raw&number=3", headers=headers)
#     # https://www.morningstar.com/stocks/xnys/ko/financials
#     screen = requests.get(f"https://www.morningstar.com/stocks/xnys/ko/financials")
#     return screen

# def get_stock_income_statement(ticker,market):
#     headers = {
#         'Referer': 'http://financials.morningstar.com/ratios/r.html?t=EXPE&region=usa&culture=en-US',
#         }
#     stockmarket = market.GET.get('market')
#     stockmarket = stockmarket.replace(" ", "+")
#     stockticker = ticker.GET.get('ticker')
#     stockticker = stockticker.replace(" ", "+")
#     screen = requests.get(f"http://financials.morningstar.com/ajax/ReportProcess4CSV.html?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&reportType=is&period=12&dataType=A&order=asc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=13805&denominatorView=raw&number=3", headers=headers)
#     return screen

# def get_stock_cash_flow(ticker,market):
#     headers = {
#         'Referer': 'http://financials.morningstar.com/ratios/r.html?t=EXPE&region=usa&culture=en-US',
#         }
#     stockmarket = market.GET.get('market')
#     stockmarket = stockmarket.replace(" ", "+")
#     stockticker = ticker.GET.get('ticker')
#     stockticker = stockticker.replace(" ", "+")
#     screen = requests.get(f"http://financials.morningstar.com/ajax/ReportProcess4CSV.html?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&reportType=cf&period=12&dataType=A&order=asc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=13805&denominatorView=raw&number=3", headers=headers)
#     # screen = requests.get(f"http://financials.morningstar.com/finan/ajax/exportKR2CSV.html?&callback=?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&order=asc", headers=headers)
#     return screen   

# def stock_history(request):
#     if 'ticker' in request.GET and 'market' in request.GET and 'type' in request.GET and 'api_key' in request.GET:
#         key_value = request.GET.get("api_key","")
#         if Profile.objects.filter(user_key__icontains=key_value):
#             ticker_value = request.GET.get("ticker", "")
#             market_value = request.GET.get("market", "")
#             type_value = request.GET.get("type", "")
        
#             html_content = get_stock_history_v1(request, request, request)
#             cont = html_content.content.decode('utf-8-sig')
#             csv = html_content.content
#             with open("newcsv.csv", "wb") as file:
#                 file.write(csv)
#             with open('newcsv.csv') as myfile:
#                 response = HttpResponse(myfile, content_type='text/csv')
#                 response['Content-Disposition'] = 'attachment; filename=stockhistory.csv'
#             x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#             if x_forwarded_for:
#                 ip = x_forwarded_for.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#             print(ip)
#             ip_res = requests.get('http://ip-api.com/json/' + ip )
#             location_data = ip_res.text
#             location_data_json = json.loads(location_data)
#             print(location_data_json)
#             if type_value == "cf":
#                 p = APIRequest(title='CASH FLOW', endpoint= "https://ancient-dawn-83050.herokuapp.com/stock_history", ticker = ticker_value, location = location_data_json, market = market_value, type = type_value)
#                 p.save()
#             elif type_value == "bs":
#                 p = APIRequest(title='BALANCE SHEET', endpoint= "https://ancient-dawn-83050.herokuapp.com/stock_history", ticker = ticker_value, location = location_data_json,market = market_value, type = type_value)
#                 p.save()
#             elif type_value == "is":
#                 p = APIRequest(title='INCOME STATEMENT', endpoint= "https://ancient-dawn-83050.herokuapp.com/stock_history", ticker = ticker_value,location = location_data_json, market = market_value, type = type_value)
#                 p.save()
#             return response
#         else:
#             return HttpResponse("REGISTER TO SEE DATA", content_type='text/json')



# def stock_history_key_ratio(request):
#     if 'ticker' in request.GET and 'market' in request.GET and 'api_key' in request.GET:
#         key_value = request.GET.get("api_key","")
#         if Profile.objects.filter(user_key__icontains=key_value):
#             html_content = get_key_ratio(request, request)
#             ticker_value = request.GET.get("ticker", "")
#             market_value = request.GET.get("market", "")
#             csv = html_content.content
#             with open("key_ratio.csv", "wb") as file:
#                 file.write(csv)
#             with open('key_ratio.csv') as myfile:
#                 response = HttpResponse(myfile, content_type='text/csv')
#                 response['Content-Disposition'] = 'attachment; filename=stockhistory.csv'

#             x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#             if x_forwarded_for:
#                 ip = x_forwarded_for.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#             print(ip)
#             ip_res = requests.get('http://ip-api.com/json/' + ip )
#             location_data = ip_res.text
#             location_data_json = json.loads(location_data)
#             print(location_data_json)
#             p = APIRequest(title='KEY RATIO', endpoint= "https://ancient-dawn-83050.herokuapp.com/stock_history_key_ratio", ticker = ticker_value, market = market_value, location = location_data_json, type = "key ratio")
#             p.save()
#             return response
#         else:
#             return HttpResponse("REGISTER TO SEE DATA", content_type='text/json')


# def stock_balance_sheet(request):
#     if 'ticker' in request.GET and 'market' in request.GET and 'api_key' in request.GET:
#         key_value = request.GET.get("api_key","")
#         if Profile.objects.filter(user_key__icontains=key_value):
#             html_content = get_balance_sheet(request, request)
#             csv = html_content.content
#             with open("balance_sheet.csv", "wb") as file:
#                 file.write(csv)
#             with open('balance_sheet.csv') as myfile:
#                 response = HttpResponse(myfile, content_type='text/csv')
#                 response['Content-Disposition'] = 'attachment; filename=stockhistory.csv'
#             x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#             if x_forwarded_for:
#                 ip = x_forwarded_for.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#             print(ip)
#             ip_res = requests.get('http://ip-api.com/json/' + ip )
#             location_data = ip_res.text
#             location_data_json = json.loads(location_data)
#             print(location_data_json)
#             p = APIRequest(title='key ratio', endpoint= "https://ancient-dawn-83050.herokuapp.com/stock_history_key_ratio?ticker=" +  str(request) , ticker = request, location = location_data_json)
#             p.save()
#             return response
#         else:
#             return HttpResponse("REGISTER TO SEE DATA", content_type='text/json')


# def testreq(ticker):
    
    
#     header = {'Connection': 'keep-alive',
#                 'Expires': '-1',
#                 'Upgrade-Insecure-Requests': '1',
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) \
#                 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
#                 }
   
#     url= (f"https://finance.yahoo.com/quote/GOOG/balance-sheet?p={ticker}")
        
#     r = requests.get(url, headers=header)
#     html = r.text
#     soup = BeautifulSoup(html, "html.parser")

#     div = soup.find_all('div', attrs={'class': 'D(tbhg)'})
#     if len(div) < 1:
#         print("Fail to retrieve table column header")
#         exit(0)

#     col = []
#     for h in div[0].find_all('span'):
#         text = h.get_text()
#         if text != "Breakdown":
#             col.append( datetime.strptime(text, "%m/%d/%Y") )
    
#     df = pd.DataFrame(columns=col)
#     for div in soup.find_all('div', attrs={'data-test': 'fin-row'}):
#         i = 0
#         idx = ""
#         val = []
#         for h in div.find_all('span'):
#             if i == 0:
#                 idx = h.get_text()
#             else:
#                 num = int(h.get_text().replace(",", "")) * 1000
#                 val.append( num )
#             i += 1
#         row = pd.DataFrame([val], columns=col, index=[idx] )
#         df = df.append(row)

#     return df

   
    

# def stock_history_all(request):
#     if 'ticker' in request.GET and 'market' in request.GET and 'api_key' in request.GET:
#         key_value = request.GET.get("api_key","")
#         if Profile.objects.filter(user_key__icontains=key_value):
#             ticker_value = request.GET.get("ticker", "")
#             market_value = request.GET.get("market", "")
#             html_content = get_key_ratio(request, request)
#             csv = html_content.content
#             with open("key_ratio.csv", "wb") as file:
#                 file.write(csv)
#             html_content_is = get_stock_balance_sheet(request, request)
#             csv = html_content_is.content
#             with open("balance_sheet.csv", "wb") as file:
#                 file.write(csv)
#             html_content_bs = get_stock_income_statement(request, request)
#             csv = html_content_bs.content
#             with open("income_statement.csv", "wb") as file:
#                 file.write(csv)
#             html_content_cf = get_stock_cash_flow(request, request)
#             csv = html_content_bs.content
#             with open("cash_flow.csv", "wb") as file:
#                 file.write(csv)
#             days = ['balance_sheet', 'cash_flow','income_statement']
#             dfs = (pd.read_csv(day + '.csv', error_bad_lines=False) for day in days)
#             pd.concat(dfs).to_csv('stock_history.csv')
#             with open('stock_history.csv') as myfile:
#                 response = HttpResponse(myfile, content_type='text/csv')
#                 response['Content-Disposition'] = 'attachment; filename=stockhistory.csv'
#             x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#             if x_forwarded_for:
#                 ip = x_forwarded_for.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#             ip_res = requests.get('http://ip-api.com/json/' +ip )
#             location_data = ip_res.text
#             location_data_json = json.loads(location_data)
#             print(location_data_json)
#             p = APIRequest(title='ALL DATA', endpoint= "https://ancient-dawn-83050.herokuapp.com/stock_history_all", ticker = ticker_value, market = market_value , location = location_data_json, type = "ALL DATA")
#             p.save()
#             return response
#         else:
#             return HttpResponse("REGISTER TO SEE DATA", content_type='text/json')

       
# ###########TO JSON#####################
# def stock_history_json(request):
#     if 'ticker' in request.GET and 'market' in request.GET and 'type' in request.GET and 'api_key' in request.GET:
#         key_value = request.GET.get("api_key","")
#         if Profile.objects.filter(user_key__icontains=key_value):
#             ticker_value = request.GET.get("ticker", "")
#             market_value = request.GET.get("market", "")
#             type_value = request.GET.get("type", "")
#             html_content = get_stock_history_v1(request, request, request)
#             cont = html_content.content.decode('utf-8-sig')
#             csv = html_content.content
#             with open("newcsv.csv", "wb") as file:
#                 file.write(csv)
#             df = pd.read_csv ('newcsv.csv',skiprows=1)
#             df.to_json ('jsonfile.json', orient='records')
#             a_file = open("jsonfile.json", "r")
#             a_json = json.load(a_file)
#             pretty_json = json.dumps(a_json).replace("null", '"0"')
#             a_file.close()
#             print(pretty_json)
#             x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#             if x_forwarded_for:
#                 ip = x_forwarded_for.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#             print(ip)
#             ip_res = requests.get('http://ip-api.com/json/' + ip )
#             location_data = ip_res.text
#             location_data_json = json.loads(location_data)
#             print(location_data_json)
#             p = APIRequest(title='INCOME STATEMENT', endpoint= "https://ancient-dawn-83050.herokuapp.com/stock_history", ticker = ticker_value, market = market_value, location = location_data_json, type = type_value)
#             p.save()
#             return HttpResponse(pretty_json, content_type='text/json')
#         else:
#             return HttpResponse("REGISTER TO SEE DATA", content_type='text/json')

# def stock_history_key_ratio_json(request):
#     if 'ticker' in request.GET and 'market' in request.GET and 'api_key' in request.GET:
#         key_value = request.GET.get("api_key","")
#         ticker_value = request.GET.get("ticker", "")
#         market_value = request.GET.get("market", "")
#         if Profile.objects.filter(user_key__icontains=key_value):
#             user_profile = Profile.objects.get(user_key=key_value)
#             user_email = user_profile.user.email
#             user_country= user_profile.country
#             html_content = get_key_ratio(request, request)
#             csv = html_content.content
#             with open("newcsv.csv", "wb") as file:
#                 file.write(csv)
#             rows_to_keep = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]
#             df = pd.read_csv ('newcsv.csv', skiprows = lambda x: x not in rows_to_keep)
#             df.replace(',','', regex=True, inplace=True)
#             df.to_json ('jsonfile.json', orient='records')
#             a_file = open("jsonfile.json", "r")
#             a_json = json.load(a_file)
#             pretty_json = json.dumps(a_json).replace("null", '"0"')
#             # parsed_data = json.loads(pretty_json)
#             a_file.close()
#             x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#             if x_forwarded_for:
#                 ip = x_forwarded_for.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#             print(ip)
#             ip_res = requests.get('http://ip-api.com/json/' + ip )
#             location_data = ip_res.text
#             location_data_json = json.loads(location_data)
#             print(location_data_json)
#             p = APIRequest(title='ALL DATA', endpoint= "https://ancient-dawn-83050.herokuapp.com/stock_history_key_ratio_json", ticker = ticker_value, market = market_value , location = location_data_json, type = "KEY RATIO JSON", user_email = user_email, user_country = user_country)
#             p.save()
        
#             return HttpResponse(pretty_json, content_type='text/json')
#         else:
#             return HttpResponse("REGISTER TO SEE DATA", content_type='text/json')


