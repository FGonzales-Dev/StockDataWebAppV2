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
    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    # driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions) 
    driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/financials")
    if download_type == "INCOME_STATEMENT":
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Income Statement')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        driver.quit()
        return 'DONE'
    elif download_type == "BALANCE_SHEET":
        WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Balance Sheet')]"))).click()
        WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        driver.quit()
        return 'DONE'
    elif download_type == "CASH_FLOW":
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expand Detail View')]"))).click()
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Data')]"))).click()
        sleep(10)
        driver.quit()
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
    data = WebDriverWait(driver_operating_perfomance, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
    data = WebDriverWait(driver_operating_perfomance, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
    df  = pd.read_html(data)    
    df[0].to_json ('operating_performance.json', orient='records')
    a_file = open("operating_performance.json", "r")
    a_file.close()
    for f in glob.iglob(BASE_DIR+'operating_performance.xls', recursive=True):
        os.remove(f)
    pd.read_json("operating_performance.json").to_excel('operating_performance.xls',index=False)
    sleep(5)
    driver_operating_perfomance.quit()
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
    data = WebDriverWait(driver_dividends, 50).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='mds-table__scroller__sal']"))).get_attribute("outerHTML")
    df  = pd.read_html(data)   
    out = df[0].to_json(orient='records') 
    sleep(10)
    driver_dividends.quit()
    return out

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
    valuation_driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    # valuation_driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions) 
    valuation_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
    if download_type == "VALUATION_CASH_FLOW": 
        valuation_driver.get(f"https://www.morningstar.com/stocks/{market_value}/{ticker_value}/valuation")
        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cash Flow')]"))).click()
        data = WebDriverWait(valuation_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-cash-flow sal-eqcss-key-stats-cash-flow']"))).get_attribute("outerHTML")
        df  = pd.read_html(data) 
        print(df[0])   
        df[0].to_json ('valuation_cash_flow.json', orient='records')
        sleep(10)
        valuation_driver.quit()   
        return 'DONE' 
    
    

    elif download_type == "VALUATION_GROWTH": 
        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Growth')]"))).click()
        data = WebDriverWait(valuation_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-growth-table sal-eqcss-key-stats-growth-table']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        df[0].to_json ('valuation_growth.json', orient='records')
        a_file = open("valuation_growth.json", "r")
        a_json = json.load(a_file)
        a_file.close()
        for f in glob.iglob(BASE_DIR+'valuation_growth.xls', recursive=True):
            os.remove(f)
        pd.read_json("valuation_growth.json").to_excel('valuation_growth.xls',index=False)
        sleep(5)
        valuation_driver.quit() 
        return 'DONE'      

        

    elif download_type == "VALUATION_FINANCIAL_HEALTH": 
        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Financial Health')]"))).click()
        data = WebDriverWait(valuation_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-financial-health sal-eqcss-key-stats-financial-health']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        df[0].to_json ('valuation_financial_health.json', orient='records')
        a_file = open("valuation_financial_health.json", "r")
        a_json = json.load(a_file)
        a_file.close()
        for f in glob.iglob(BASE_DIR+'valuation_financial_health.xls', recursive=True):
            os.remove(f)
        pd.read_json("valuation_financial_health.json").to_excel('valuation_financial_health.xls',index=False)
        sleep(5)
        valuation_driver.quit()  
        return 'DONE'    

    elif download_type == "VALUATION_OPERATING_EFFICIENCY":
        WebDriverWait(valuation_driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Operating and Efficiency')]"))).click()
        data = WebDriverWait(valuation_driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='sal-component-ctn sal-component-key-stats-oper-efficiency sal-eqcss-key-stats-oper-efficiency']"))).get_attribute("outerHTML")
        df  = pd.read_html(data)    
        df[0].to_json('valuation_operating_efficiency.json', orient='records')
        a_file = open("valuation_operating_efficiency.json", "r")
        a_json = json.load(a_file)
        for f in glob.iglob(BASE_DIR+'valuation_operating_efficiency.xls', recursive=True):
            os.remove(f)
        pd.read_json("valuation_operating_efficiency.json").to_excel('valuation_operating_efficiency.xls',index=False)
        a_file.close()
        sleep(5)
        valuation_driver.quit()      


