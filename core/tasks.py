import json
from celery import shared_task
from celery_progress.backend import ProgressRecorder

from django.http import HttpResponse

import os
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from cb_dj_weather_app.settings import BASE_DIR
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from time import sleep
import glob

import pyrebase
import os
from multiprocessing.pool import ThreadPool
from functools import partial

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

def format_dict(d):
    vals = list(d.values())
    return "={},".join(d.keys()).format(*vals) + "={}".format(vals[-1])

@shared_task(bind=True)
def scraper(self,ticker_value,market_value,download_type):
    CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
    prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option('prefs', prefs)
    chromeOptions.add_argument("--disable-infobars")
    chromeOptions.add_argument("--start-maximized")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("--window-size=1920,1080")
    chromeOptions.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chromeOptions.add_argument('--no-sandbox')   
    chromeOptions.add_argument("--disable-dev-shm-usage")
    # driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions) 
    driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
    if download_type == "INCOME_STATEMENT":
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Income Statement')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)

        try:
            excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Income Statement_Annual_As Originally Reported.xls")
            data1 = excel_data_df.to_json()
            print(data1)
            database.child("income_statement").set({"income_statement": data1 })
        except:
            x =  '{"income_statement":{"none":"no data"}}'
            database.child("income_statement").set({"income_statement": x })
        sleep(10)
        driver.quit()
        return 'DONE'
    elif download_type == "BALANCE_SHEET":
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Balance Sheet')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        try:
            excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Balance Sheet_Annual_As Originally Reported.xls")
            data1 = excel_data_df.to_json()
            print(data1)
            database.child("balance_sheet").set({"balance_sheet": data1 })
        except:
            x =  '{"balance_sheet":{"none":"no data"}}'
            database.child("balance_sheet").set({"balance_sheet": x })
        sleep(10)
        driver.quit()
        return 'DONE'
    elif download_type == "CASH_FLOW":
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        try:
            excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Cash Flow_Annual_As Originally Reported.xls")
            data1 = excel_data_df.to_json()
            print(data1)
            database.child("cash_flow").set({"cash_flow": data1 })
        except:
            x =  '{"cash_flow":{"none":"no data"}}'
            database.child("cash_flow").set({"cash_flow": x })
        sleep(10)
        driver.quit()
        return 'DONE'

@shared_task()
def scraper_dividends(ticker_value,market_value):
    CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
    prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option('prefs', prefs)
    chromeOptions.add_argument('--headless')
    chromeOptions.add_argument("--window-size=1920,1080")
    chromeOptions.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chromeOptions.add_argument('--disable-setuid-sandbox')
    chromeOptions.add_argument('--remote-debugging-port=9222')
    chromeOptions.add_argument('--disable-extensions')
    chromeOptions.add_argument('start-maximized')
    chromeOptions.add_argument('--disable-gpu')
    chromeOptions.add_argument('--no-sandbox')
    chromeOptions.add_argument('--disable-dev-shm-usage')
    # driver_dividends = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    driver_dividends = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)
    driver_dividends.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/dividends")
    try:
        data = WebDriverWait(driver_dividends, 50).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)   
        data1 = df[0].to_json()
        print(data1)
        database.child("dividends").set({"dividends": data1 })
    except:
        x =  '{"dividends":{"none":"no data"}}'
        database.child("dividends").set({"dividends": x })
    sleep(10)
    driver_dividends.quit()
    return 'DONE'

@shared_task()
def scraper_valuation(ticker_value,market_value,download_type):
    CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
    prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option('prefs', prefs)
    chromeOptions.add_argument('--headless')
    chromeOptions.add_argument("--window-size=1920,1080")
    chromeOptions.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chromeOptions.add_argument('--disable-setuid-sandbox')
    chromeOptions.add_argument('--remote-debugging-port=9222')
    chromeOptions.add_argument('--disable-extensions')
    chromeOptions.add_argument('start-maximized')
    chromeOptions.add_argument('--disable-gpu')
    chromeOptions.add_argument('--no-sandbox')
    chromeOptions.add_argument('--disable-dev-shm-usage')
    # valuation_driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    valuation_driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions) 
    valuation_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
    if download_type == "VALUATION_CASH_FLOW": 
        valuation_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
        try: 
            data = WebDriverWait(valuation_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-button__sal mds-button--secondary__sal mds-button--small__sal']"))).get_attribute("outerHTML")
            df  = pd.read_html(data) 
            print(data)
            data1 = df[0].to_json()
            print(data1)
            database.child("valuation_cash_flow").set({"valuation_cash_flow": data1 })
        except:
            x =  '{"valuation_cash_flow":{"none":"no data"}}'
            database.child("valuation_cash_flow").set({"valuation_cash_flow": x })
            sleep(5)
        valuation_driver.quit()   
        return 'DONE'
    elif download_type == "VALUATION_GROWTH": 
        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Growth')]"))).click()
        try:
            data = WebDriverWait(valuation_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-button__sal mds-button--secondary__sal mds-button--small__sal']"))).get_attribute("outerHTML")
            df  = pd.read_html(data)    
            data1 = df[0].to_json()
            print(data1)
            database.child("valuation_growth").set({"valuation_growth": data1 })
        except:
            x =  '{"valuation_growth":{"none":"no data"}}'
            database.child("valuation_growth").set({"valuation_growth": x })
        sleep(5)
        valuation_driver.quit() 
        return 'DONE'      
    elif download_type == "VALUATION_FINANCIAL_HEALTH": 
        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Financial Health')]"))).click()
        try:
            data = WebDriverWait(valuation_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-button__sal mds-button--secondary__sal mds-button--small__sal']"))).get_attribute("outerHTML")
            df  = pd.read_html(data)    
            data1 = df[0].to_json()
            print(data1)
            database.child("valuation_financial_health").set({"valuation_financial_health": data1 })
        except:
            x =  '{"valuation_financial_health":{"none":"no data"}}'
            database.child("valuation_financial_health").set({"valuation_financial_health": x })
        sleep(5)
        valuation_driver.quit()  
        return 'DONE'    
    elif download_type == "VALUATION_OPERATING_EFFICIENCY":
        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Operating and Efficiency')]"))).click()
        try:
            data = WebDriverWait(valuation_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-button__sal mds-button--secondary__sal mds-button--small__sal']"))).get_attribute("outerHTML")
            
            # mds-button__sal mds-button--secondary__sal mds-button--small__sal
            
            
            df  = pd.read_html(data)
            data1 = df[0].to_json()
            print(data1)
            database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": data1 })
        except:
             x =  '{"valuation_operating_efficiency":{"none":"no data"}}'
             database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": x })
        sleep(5)
        valuation_driver.quit() 
        return 'DONE'       

@shared_task(bind=True)
def all_scraper(self,ticker_value,market_value):
    CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
    prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option('prefs', prefs)
    chromeOptions.add_argument('--headless')
    chromeOptions.add_argument("--window-size=1920,1080")
    chromeOptions.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chromeOptions.add_argument('--disable-setuid-sandbox')
    chromeOptions.add_argument('--remote-debugging-port=9222')
    chromeOptions.add_argument('--disable-extensions')
    chromeOptions.add_argument('start-maximized')
    chromeOptions.add_argument('--disable-gpu')
    chromeOptions.add_argument('--no-sandbox')
    chromeOptions.add_argument('--disable-dev-shm-usage')
    # valuation_financial_health_driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    valuation_financial_health_driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions) 
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
    WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Financial Health')]"))).click()
    try:
        data = WebDriverWait(valuation_financial_health_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-financial-health sal-eqcss-key-stats-financial-health']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        data1 = df[0].to_json()
        print(data1)
        database.child("valuation_financial_health").set({"valuation_financial_health": data1 })
    except:
         x =  '{"valuation_financial_health":{"none":"no data"}}'
         database.child("valuation_financial_health").set({"valuation_financial_health": x })
    sleep(10)
    WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Operating and Efficiency')]"))).click()
    try:
        data = WebDriverWait(valuation_financial_health_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-oper-efficiency sal-eqcss-key-stats-oper-efficiency']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)
        data1 = df[0].to_json()
        print(data1)
        database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": data1 })
    except:
        x =  '{"valuation_operating_efficiency":{"none":"no data"}}'
        database.child("valuation_operating_efficiency").set({"valuation_operating_efficiency": x })
    sleep(10)
    WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
    try:
        data = WebDriverWait(valuation_financial_health_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-cash-flow sal-eqcss-key-stats-cash-flow']"))).get_attribute("outerHTML")
        df  = pd.read_html(data) 
        print(data)
        data1 = df[0].to_json()
        print(data1)
        database.child("valuation_cash_flow").set({"valuation_cash_flow": data1 })
    except:
        x =  '{"valuation_cash_flow":{"none":"no data"}}'
        database.child("valuation_cash_flow").set({"valuation_cash_flow": x })
    sleep(10)    
    WebDriverWait(valuation_financial_health_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Growth')]"))).click()
    try:
        data = WebDriverWait(valuation_financial_health_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-growth-table sal-eqcss-key-stats-growth-table']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        data1 = df[0].to_json()
        print(data1)
        database.child("valuation_growth").set({"valuation_growth": data1 })
    except:
        x =  '{"valuation_growth":{"none":"no data"}}'
        database.child("valuation_growth").set({"valuation_growth": x })

    sleep(10)
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/performance")
    try:
        data = WebDriverWait(valuation_financial_health_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        data1 = df[0].to_json()
        print(data1)
        database.child("operating_performance").set({"operating_performance": data1 })
    except:
         x =  '{"operating_performance":{"none":"no data"}}'
         database.child("operating_performance").set({"operating_performance": x })

    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/dividends")
    try:
        data = WebDriverWait(valuation_financial_health_driver, 50).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)   
        data1 = df[0].to_json()
        print(data1)
        database.child("dividends").set({"dividends": data1 })
    except:
        x =  '{"dividends":{"none":"no data"}}'
        database.child("dividends").set({"dividends": x })
    sleep(10)
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
    sleep(10)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Income Statement')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
    sleep(10)
    try:
        excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Income Statement_Annual_As Originally Reported.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("income_statement").set({"income_statement": data1 })
    except:
        x =  '{"income_statement":{"none":"no data"}}'
        database.child("income_statement").set({"income_statement": x })
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Balance Sheet')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
    sleep(10)
    try:
            excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Balance Sheet_Annual_As Originally Reported.xls")
            data1 = excel_data_df.to_json()
            print(data1)
            database.child("balance_sheet").set({"balance_sheet": data1 })
    except:
        x =  '{"balance_sheet":{"none":"no data"}}'
        database.child("balance_sheet").set({"balance_sheet": x })
    valuation_financial_health_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
    sleep(5)
    WebDriverWait(valuation_financial_health_driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
    sleep(10)
    try:
        excel_data_df = pd.read_excel(BASE_DIR + "/selenium/Cash Flow_Annual_As Originally Reported.xls")
        data1 = excel_data_df.to_json()
        print(data1)
        database.child("cash_flow").set({"cash_flow": data1 })
    except:
        x =  '{"cash_flow":{"none":"no data"}}'
        database.child("cash_flow").set({"cash_flow": x })
    sleep(10)
    valuation_financial_health_driver.quit() 
    return 'DONE'    



@shared_task()
def scraper_operating_performance(ticker_value, market_value):
    CHROME_DRIVER_PATH = BASE_DIR+"/chromedriver"
    prefs = {'download.default_directory' :  BASE_DIR + "/selenium"}
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option('prefs', prefs)
    chromeOptions.add_argument('--headless')
    chromeOptions.add_argument("--window-size=1920,1080")
    chromeOptions.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chromeOptions.add_argument('--disable-setuid-sandbox')
    chromeOptions.add_argument('--remote-debugging-port=9222')
    chromeOptions.add_argument('--disable-extensions')
    chromeOptions.add_argument('start-maximized')
    chromeOptions.add_argument('--disable-gpu')
    chromeOptions.add_argument('--no-sandbox')
    chromeOptions.add_argument('--disable-dev-shm-usage')
    # driver_operating_perfomance = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    driver_operating_perfomance = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)
    driver_operating_perfomance.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/performance")
    try:
        data = WebDriverWait(driver_operating_perfomance, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        data1 = df[0].to_json()
        print(data1)
        database.child("operating_performance").set({"operating_performance": data1 })
    except:
        x =  '{"operating_performance":{"none":"no data"}}'
        database.child("operating_performance").set({"operating_performance": x })
    sleep(10)
    driver_operating_perfomance.quit()
    return 'DONE'

