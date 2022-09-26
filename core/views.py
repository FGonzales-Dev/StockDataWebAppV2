
from django.shortcuts import render
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
from time import time

# Create your views here.

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def Convert(lst):
    it = iter(lst)
    res_dct = dict(zip(it, it))
    return res_dct

def flatten(lis):
     for item in lis:
         if isinstance(item, Iterable) and not isinstance(item, str):
             for x in flatten(item):
                 yield x
         else:        
             yield item


def get_html_content(request):
    ticker = request.GET.get('ticker')
    ticker = ticker.replace(" ", "+")
    screen = requests.get(f'https://finviz.com/quote.ashx?t={ticker}', headers = headers).text
    return screen

####dell
#     http://financials.morningstar.com/ajax/ReportProcess4HtmlAjax.html?&t=XNYS:IBM&region=usa&culture=en-US&cur=&reportType=bs&period=12&dataType=A&order=desc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=901340&callback=jsonp1626182303790&_=1626182305262

# ###aapl
# http://financials.morningstar.com/ajax/ReportProcess4HtmlAjax.html?&t=XNAS:AAPL&region=usa&culture=en-US&cur=&reportType=bs&period=12&dataType=A&order=desc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=603343&callback=jsonp1626182397784&_=1626182398552

def csv_to_json(csvFilePath, jsonFilePath):
    jsonArray = []
    csvFilePath = r'newcsv.csv'
    jsonFilePath = r'jsonfile.json'
    #read csv file
    with open(csvFilePath, encoding='utf-8-sig') as csvf: 
        #load csv file data using csv library's dictionary reader
        csvReader = csv.DictReader(csvf) 
        
        #convert each csv row into python dict
        for row in csvReader: 
            #add this python dict to json array 
            jsonArray.append(row)
  
    #convert python jsonArray to JSON String and write to file
    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf: 
        jsonString = json.dumps(jsonArray, indent=4)
        jsonf.write(jsonString)
          
    
   
def get_stock_history_v1(ticker,market ,type):
    headers = {
        'Referer': 'http://financials.morningstar.com/ratios/r.html?t=EXPE&region=usa&culture=en-US',
        }
    stockmarket = market.GET.get('market')
    stockmarket = stockmarket.replace(" ", "+")
    stockticker = ticker.GET.get('ticker')
    stockticker = stockticker.replace(" ", "+")
    stocktype = type.GET.get('type')
    stocktype = stocktype.replace(" ", "+")
    print("stockmarket")
    print(stockmarket)
    print("stockticker")
    print(stockticker)
    
    screen = requests.get(f"http://financials.morningstar.com/ajax/ReportProcess4CSV.html?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&reportType={stocktype}&period=12&dataType=A&order=asc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=13805&denominatorView=raw&number=3", headers=headers)
    # screen = requests.get(f"http://financials.morningstar.com/finan/ajax/exportKR2CSV.html?&callback=?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&order=asc", headers=headers)
    return screen
   

def test_income_statement(request):
    if 'ticker' in request.GET and 'market' in request.GET:
        print(request)
        html_content = get_income_statement(request, request)
        cont = html_content.content.decode('utf-8-sig')
        csv = html_content.content
        with open("newcsv.csv", "wb") as file:
            file.write(csv)

        with open('newcsv.csv') as myfile:
            response = HttpResponse(myfile, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=stockhistory.csv'
        return response
   


def test_stock_history(request):
    if 'ticker' in request.GET and 'market' in request.GET and 'type' in request.GET:
        print(request)
        html_content = get_stock_history_v1(request, request, request)
        cont = html_content.content.decode('utf-8-sig')
        csv = html_content.content

       
        with open("newcsv.csv", "wb") as file:
            file.write(csv)
        with open('newcsv.csv') as myfile:
            response = HttpResponse(myfile, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=stockhistory.csv'
        return response




    
def get_balance_sheet(ticker,market ):
    stockmarket = market.GET.get('market')
    stockmarket = stockmarket.replace(" ", "+")
    stockticker = ticker.GET.get('ticker')
    stockticker = stockticker.replace(" ", "+")
    print("stockmarket")
    print(stockmarket)
    print("stockticker")
    print(stockticker)
    screen = requests.get(f'http://financials.morningstar.com/ajax/ReportProcess4HtmlAjax.html?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&reportType=bs&period=12&dataType=A&order=desc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=360489&callback=jsonp1625804201679&_=1625804203482')
    return screen

def get_income_statement(ticker,market):
    stockmarket = market.GET.get('market')
    stockmarket = stockmarket.replace(" ", "+")
    stockticker = ticker.GET.get('ticker')
    stockticker = stockticker.replace(" ", "+")
    print("stockmarket")
    print(stockmarket)
    print("stockticker")
    print(stockticker)
    screen = requests.get(f'http://financials.morningstar.com/ajax/ReportProcess4HtmlAjax.html?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&reportType=is&period=12&dataType=A&order=desc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=705147&callback=jsonp1626181853126&_=1626181854645')
    return screen


def get_cash_flow(ticker,market):
    stockmarket = market.GET.get('market')
    stockmarket = stockmarket.replace(" ", "+")
    stockticker = ticker.GET.get('ticker')
    stockticker = stockticker.replace(" ", "+")
    print("stockmarket")
    print(stockmarket)
    print("stockticker")
    print(stockticker)
    screen = requests.get(f'http://financials.morningstar.com/ajax/ReportProcess4HtmlAjax.html?&t={stockmarket}:{stockticker}&region=usa&culture=en-US&cur=&reportType=cf&period=12&dataType=A&order=desc&columnYear=5&curYearPart=1st5year&rounding=3&view=raw&r=770409&callback=jsonp1626097045909&_=1626097048062')
    return screen


def stock_balance_sheet(request):
    data_param = [
           "net_cash_provided_by_o...",
            "Net_income",
            "Depreciation_&_amortiz...",
            "Deferred_income_taxes",
            "Stock_based_compensati...",
            "Change_in_working_capi...",
            "Inventory",
            "Prepaid_expenses",
            "Accounts_payable",
            "Income_taxes_payable",
            "Other_working_capital",
            "Other_non-cash_items",
            "Net_cash_used_for_inve...",
            "Investments_in_propert...",
            "Property,_plant,_and_e...",
            "Acquisitions,_net",
            "Purchases_of_investmen...",
            "Sales/Maturities_of_in...",
            "Other_investing_activi...",
            "Net_cash_provided_by_(...",
            "Debt_issued",
            "Debt_repayment",
            "Preferred_stock_repaid",
            "Common_stock_repurchas...",
            "Excess_tax_benefit_fro...",
            "Dividend_paid",
            "Other_financing_activi...",
            "Effect_of_exchange_rat...",
            "Net_change_in_cash",
            "Cash_at_beginning_of_p..",
            "Cash_at_end_of_period",
            "Free_Cash_Flow",
            "Operating_cash_flow",
            "Capital_expenditure",
            "Free_cash_flow"]

    data = dict()
    finalData = list()
    if 'ticker' in request.GET and 'market' in request.GET:
        html_content = get_balance_sheet(request, request)
        cont = html_content.content.decode('utf-8')
        jsn = loads(cont[cont.find("{"):cont.rfind("}") + 1])
        soup = BeautifulSoup(jsn["result"])
        soup.select_one("div.r_xcmenu.rf_table")
        headers = [d.text for d in soup.select("div.rf_header [id^=Y_]")]
        result = list()
        print(headers)
            

        #FIX THIS AREA
        data_name  = [  "Total_assets",
                        "Total current assets",
                        "Total cash",
                        "Cash and cash equivalent",
                        "Short-term investments",
                        "Receivables", 
                        "Inventories ",
                        "Other current assets", 
                        "Total non-current assets", 
                        "Net property, plant an", 
                        "Gross property, plant", 
                        "Accumulated Depreciation",
                        "Equity and other investment", 
                        "Goodwill", 
                        "Intangible assets", 
                        "Other long-term assets", 
                        "Total Assets", 
                        "Total liabilities", 
                        "Total current liabilities", 
                        "Short-term debt", 
                        "Accounts payable", 
                        "Accrued liabilities", 
                        "Deferred revenues", 
                        "Other current liabilities", 
                        "Total non-current liabilities", 
                        "Long-term debt", 
                        "Deferred taxes liabilities", 
                        "Deferred revenues", 
                        "Other long-term liabilities",
                        "Total stockholders’ equity", 
                        "Common  stock", 
                        "Retained earnings", 
                        "Accumulated other com"]

        for row in soup.find_all("div","rf_crow", style=False):
            print([d.text for d in row.select("[id^=Y_]")])
            result.append([d.text for d in row.select("[id^=Y_]")])
            reverse = list(map(list, zip(*result)))
        headers.insert(0,"year")
        headers.insert(1,"data_name")
        data[headers[0]]= dict(zip(headers,headers ))
        data[headers[1]]= dict(zip(data_param,data_name ))
        data[headers[2]]= dict(zip(data_param,reverse[0] ))
        data[headers[3]] = dict(zip(data_param,reverse[1] ))
        data[headers[4]] = dict(zip(data_param,reverse[2] ))
        data[headers[5]] = dict(zip(data_param,reverse[3] ))
        data[headers[6]] = dict(zip(data_param,reverse[4] ))
        finalData.append(data)
        finalResponse= json.dumps({ 'data': finalData})
    return HttpResponse(finalResponse, content_type='text/json')

def stock_cash_flow(request):
    finalData = list()
    
    if 'ticker' in request.GET and 'market' in request.GET:
        html_content = get_cash_flow(request,request)
        cont = html_content.content.decode('utf-8')
        jsn = loads(cont[cont.find("{"):cont.rfind("}") + 1])
        soup = BeautifulSoup(jsn["result"])
        soup.select_one("div.r_xcmenu.rf_table")
        headers = [d.text for d in soup.select("div.rf_header [id^=Y_]")]
        result = list()
        print(headers)
        data_name = [
            "Net cash provided by o...",
            "Net income",
            "Depreciation & amortiz...",
            "Deferred income taxes",
            "Stock based compensati...",
            "Change in working capi...",
            "Inventory",
            "Prepaid expenses",
            "Accounts payable",
            "Income taxes payable",
            "Other working capital",
            "Other non-cash items",
            "Net cash used for inve...",
            "Investments in propert...",
            "Property, plant, and e...",
            "Acquisitions, net",
            "Purchases of investmen...",
            "Sales/Maturities of in...",
            "Other investing activi...",
            "Net cash provided by (...", 
            "Debt issued",
            "Debt repayment",
            "Preferred stock repaid",
            "Common stock repurchas...",
            "Excess tax benefit fro...",
            "Dividend paid",
            "Other financing activi...",
            "Effect of exchange rat...",
            "Net change in cash",
            "Cash at beginning of p..",
            "Cash at end of period",
            "Free Cash Flow",
            "Operating cash flow",
            "Capital expenditure",
            "Free cash flow"]
        for row in soup.find_all("div","rf_crow", style=False):
            print([d.text for d in row.select("[id^=Y_]")])
            result.append([d.text for d in row.select("[id^=Y_]")])
        reverse = list(map(list, zip(*result)))
        data = dict()
        data0 = dict(zip(data_name,reverse[0] ))
        data1 = dict(zip(data_name,reverse[1] ))
        # data[headers[2]] = dict(zip(data_name,reverse[2] ))
        # data[headers[3]] = dict(zip(data_name,reverse[3] ))
        # data[headers[4]] = dict(zip(data_name,reverse[4] ))
        finalData.append(data0)
        finalData.append(data1)
        finalResponse= json.dumps({ 'data': finalData})
    return HttpResponse(finalResponse, content_type='text/json')

def stock_income_statement(request):
    data = dict()
    finalData = list()
    if 'ticker' in request.GET and 'market' in request.GET:
        html_content = get_income_statement(request,request)
        cont = html_content.content.decode('utf-8')
        jsn = loads(cont[cont.find("{"):cont.rfind("}") + 1])
        soup = BeautifulSoup(jsn["result"])
        soup1 = BeautifulSoup(jsn["result"])
        soup.select_one("div.r_xcmenu.rf_table")
        soup1.select_one("div.r_xcmenu.rf_table_left")
        headers = [d.text for d in soup.select("div.rf_header [id^=Y_]")]
        result = list()
        data_name = list()
        print(headers)
    

        # result.append(headers)
        for row in soup.find_all("div","rf_crow", style=False):
            # print([d.text for d in row.select("[id^=Y_]")])
            result.append([d.text for d in row.select("[id^=Y_]")])
            reverse = list(map(list, zip(*result)))


        for row in soup1.find_all("div","rf_crow1", style="_height:16px; _float:none;"):
            data_name.append(row.text)
        # data_name.insert(0,"year")
        # headers.insert(0,"data_name")
        # data[headers[0]]= dict(zip(data_name,data_name ))
        # data[headers[1]]= dict(zip(data_name,reverse[0] ))
        # data[headers[2]] = dict(zip(data_name,reverse[1] ))
        # data[headers[3]] = dict(zip(data_name,reverse[2] ))
        # data[headers[4]] = dict(zip(data_name,reverse[3] ))
        # data[headers[5]] = dict(zip(data_name,reverse[4] ))
        # data[headers[6]] = dict(zip(data_name,reverse[5] ))
        
        dataNameCount = 0
        for i in data_name:
            print(i)
            data = dict(zip(data_name,result))
            

        finalData.append(data)
        finalResponse= json.dumps({ 'data': data})
    return HttpResponse(finalResponse, content_type='text/json')





#CLEAN DO NOT DELETE


def print_table(soup):
    for i, tr in enumerate(soup.select('tr')):
        row_data = [td.text for td in tr.select('td, th') if td.text]
        if not row_data:
            continue
        if len(row_data) < 12:
            row_data = ['X'] + row_data
        for j, td in enumerate(row_data):
            if j==0:
                print('{: >30}'.format(td), end='|')
            else:
                print('{: ^12}'.format(td), end='|')
        print()


def stockhistory(request):
    if 'ticker' in request.GET:
        ticker = request.GET.get('ticker')
        ticker = ticker.replace(" ", "+")
        url1 = 'http://financials.morningstar.com/finan/financials/getFinancePart.html?&callback=xxx&t={ticker}'
        soup1 = BeautifulSoup(json.loads(re.findall(r'xxx\((.*)\)', requests.get(url1).text)[0])['componentData'], 'lxml')
        print_table(soup1)
        print()
    
def home(request, data_param):
    result = list()
    resultTitle = list()
    finalRest = None
    #if 'datastock' in request.GET:
    tens = dict(k=10e3, m=10e5, b=10e8)
    convertNumAbbv = lambda x : int(float(x[0:-1]) * tens[x[-1].lower()])

    if 'ticker' in request.GET:
        html_content = get_html_content(request)
        soup = BeautifulSoup(html_content, 'html.parser')
        sptable = soup.table
        sptitle = soup.table
        sptable = soup.find("table", { "class" : "snapshot-table2" })
        sptitle = soup.find("table", { "class": "fullview-title" })

        sptitle_rows = sptitle.find_all('tr')
        for tr in sptitle_rows:
            td = tr.find_all('td')
            row = [i.text for i in td]
            resultTitle.append(row)
           
            

        table_rows = sptable.find_all('tr')
        for tr in table_rows:
            td = tr.find_all('td')
            row = [i.text for i in td]
            result.append(row)
        finaldict = {}
        
        
        flattenList = list(flatten(result))
        finalRest =  Convert(flattenList)
        finalRest = dict((k, v) for k, v in finalRest.items())

        titleDict = {
        "name": str(resultTitle[1]).replace('|', '').replace('[','').replace(']','').replace("'", ""),
        "industry": str(resultTitle[2]).replace('[','').replace(']','').replace("'", "")
        }

        titleDict.update(finalRest)
        
        li = list(data_param.split(","))
   
        name = titleDict.get("name")
        industry = titleDict.get("industry")
        shs_outstand = finalRest.get("Shs Outstand")
        perf_week = finalRest.get("Perf Week")
        pe = finalRest.get("P/E")
        eps_ttm = finalRest.get("EPS (ttm)")
        insider_own = finalRest.get("Insider Own")
        market_cap = finalRest.get("Market Cap")
        forward_pe = finalRest.get("Forward P/E")
        eps_next_y = finalRest.get("EPS next Y")
        insider_trans = finalRest.get("Insider Trans")
        shs_float = finalRest.get("Shs Float")
        perf_month = finalRest.get("Perf Month")
        income = finalRest.get("Income")
        peg = finalRest.get("PEG")
        eps_next_q = finalRest.get("EPS next Q")
        inst_own = finalRest.get("Inst Own")
        short_float = finalRest.get("Short Float")
        perf_quarter = finalRest.get("Perf Quarter")
        sales = finalRest.get("Sales")
        ps = finalRest.get("P/S")
        eps_this_y = finalRest.get("EPS this Y")
        inst_trans = finalRest.get("Inst Trans")
        short_ratio = finalRest.get("Short Ratio")
        perf_half_y = finalRest.get("Perf Half Y")
        book_sh = finalRest.get("Book/sh")
        pb  = finalRest.get("P/B")
        roa = finalRest.get("ROA")
        target_price = finalRest.get("Target Price")
        perf_year = finalRest.get("Perf Year")
        cash_sh = finalRest.get("Cash/sh")
        pc = finalRest.get("P/C")
        eps_next_5y = finalRest.get("EPS next 5Y")
        roe = finalRest.get("ROE")
        range_52w = finalRest.get("52W Range")
        perf_ytd = finalRest.get("Perf YTD")
        dividend = finalRest.get("Dividend")
        quick_ratio = finalRest.get("Quick Ratio")
        eps_past_5y = finalRest.get("EPS past 5Y")
        roi = finalRest.get("ROI")
        high_52w = finalRest.get("52W High")
        beta = finalRest.get("Beta")
        dividend_percent = finalRest.get("Dividend %")
        sales_past_5y = finalRest.get("Sales past 5Y")
        gross_margin = finalRest.get("Gross Margin")
        low_52w = finalRest.get("52W Low")
        atr = finalRest.get("ATR")
        employees = finalRest.get("Employees")
        current_ratio = finalRest.get("Current Ratio")
        sales_qq = finalRest.get("Sales Q/Q")
        oper_margin = finalRest.get("Oper. Margin")
        rsi_14 = finalRest.get("RSI (14)")
        volatility = finalRest.get("Volatility")
        optionable = finalRest.get("Optionable")
        lt_debt_eq = finalRest.get("LT Debt/Eq")
        eps_qq = finalRest.get("EPS Q/Q")
        profit_margin = finalRest.get("Profit Margin")
        rel_volume = finalRest.get("Rel Volume")
        prev_close = finalRest.get("Prev Close")
        shortable = finalRest.get("Shortable")
        earnings = finalRest.get("Earnings")
        payout = finalRest.get("Payout")
        avg_volume = finalRest.get("Avg Volume")
        price = finalRest.get("Price")
        recom = finalRest.get("Recom")
        sma_20 = finalRest.get("SMA20")
        sma_50 = finalRest.get("SMA50")
        sma_200 = finalRest.get("SMA200")
        volume = finalRest.get("Volume")
        change = finalRest.get("Change")
        for i in li:
            val = finalRest.get(i)
            if i == "shs_outstand": 
                 finaldict["Shs Outstand"] = convertNumAbbv(shs_outstand) 
            elif i == "perf_week":
                finaldict["Perf Week"] = perf_week
            elif i == "pe":
                finaldict["P/E"] = pe  
            elif i == "eps_ttm":
                finaldict["EPS (ttm)"] = eps_ttm  
            elif i == "insider_own":
                finaldict["Insider Own"] = insider_own  
            elif i == "market_cap":
                finaldict["Market Cap"] = convertNumAbbv(market_cap)  
            elif i == "forward_pe":
                finaldict["Forward P/E"] = forward_pe  
            elif i == "eps_next_y":
                finaldict["EPS next Y"] = eps_next_y  
            elif i == "insider_trans":
                finaldict["Insider Trans"] = insider_trans  
            elif i == "shs_float":
                finaldict["Shs Float"] = convertNumAbbv(shs_float)  
            elif i == "perf_month":
                finaldict["Perf Month"] = perf_month 
            elif i == "income":
                finaldict["Income"] = convertNumAbbv(income)  
            elif i == "peg":
                finaldict["PEG"] = peg  
            elif i == "eps_next_q":
                finaldict["EPS next Q"] = eps_next_q  
            elif i == "inst_own":
                finaldict["Inst Own"] = inst_own  
            elif i == "short_float":
                finaldict["Short Float"] = short_float
            elif i == "perf_quarter":
                finaldict["Perf Quarter"] = perf_quarter
            elif i == "sales":
                finaldict["Sales"] = convertNumAbbv(sales)
            elif i == "ps":
                finaldict["P/S"] = ps
            elif i == "eps_this_y":
                finaldict["EPS this Y"] = eps_this_y
            elif i == "inst_trans":
                finaldict["Inst Trans"] = inst_trans
            elif i == "short_ratio":
                finaldict["Short Ratio"] = short_ratio
            elif i == "perf_half_y":
                finaldict["Perf Half Y"] = perf_half_y
            elif i == "book_sh":
                finaldict["Book/sh"] = book_sh
            elif i == "pb":
                finaldict["P/B"] = pb
            elif i == "roa":
                finaldict["ROA"] = roa   
            elif i == "target_price":
                finaldict["Target Price"] = target_price  
            elif i == "perf_year":
                finaldict["Perf Year"] = perf_year      
            elif i == "cash_sh":
                finaldict["Cash/sh"] = cash_sh  
            elif i == "pc":
                finaldict["P/C"] = pc  
            elif i == "eps_next_5y":
                finaldict["EPS next 5Y"] = eps_next_5y
            elif i == "roe":
                finaldict["ROE"] = roe      
            elif i == "range_52w":
                finaldict["52W Range"] = range_52w  
            elif i == "perf_ytd":
                finaldict["Perf YTD"] = perf_ytd  
            elif i == "dividend":
                finaldict["Dividend"] = dividend  
            elif i == "quick_ratio":
                finaldict["Quick Ratio"] = quick_ratio      
            elif i == "eps_past_5y":
                finaldict["EPS past 5Y"] = eps_past_5y  
            elif i == "roi":
                finaldict["ROI"] = roi  
            elif i == "high_52w":
                finaldict["52W High"] = high_52w  
            elif i == "beta":
                finaldict["Beta"] = beta  
            elif i == "dividend_percent":
                finaldict["Dividend %"] = dividend_percent  
            elif i == "sales_past_5y":
                finaldict["Sales past 5Y"] = sales_past_5y  
            elif i == "gross_margin":
                finaldict["Gross Margin"] = gross_margin  
            elif i == "low_52w":
                finaldict["52W Low"] = low_52w     
            elif i == "atr":
                finaldict["ATR"] = atr  
            elif i == "employees":
                finaldict["Employees"] = employees  
            elif i == "current_ratio":
                finaldict["Current Ratio"] = current_ratio  
            elif i == "sales_qq":
                finaldict["Sales Q/Q"] = sales_qq  
            elif i == "oper_margin":
                finaldict["Oper. Margin"] = oper_margin  
            elif i == "rsi_14":
                finaldict["RSI (14)"] = rsi_14  
            elif i == "volatility":
                finaldict["Volatility"] = volatility  
            elif i == "optionable":
                finaldict["Optionable"] = optionable  
            elif i == "lt_debt_eq":
                finaldict["LT Debt/Eq"] = lt_debt_eq  
            elif i == "eps_qq":
                finaldict["EPS Q/Q"] = eps_qq  
            elif i == "profit_margin":
                finaldict["Profit Margin"] = profit_margin  
            elif i == "beta":
                finaldict["Rel Volume"] = beta  
            elif i == "rel_volume":
                finaldict["Beta"] = rel_volume  
            elif i == "prev_close":
                finaldict["Prev Close"] = prev_close  
            elif i == "beta":
                finaldict["Shortable"] = beta  
            elif i == "shortable":
                finaldict["Beta"] = shortable  
            elif i == "earnings":
                finaldict["Earnings"] = earnings  
            elif i == "payout":
                finaldict["Payout"] = payout  
            elif i == "avg_volume":
                finaldict["Avg Volume"] = convertNumAbbv(avg_volume)  
            elif i == "price":
                finaldict["Price"] = price  
            elif i == "recom":
                finaldict["Recom"] = recom  
            elif i == "sma_20":
                finaldict["SMA20"] = sma_20  
            elif i == "sma_50":
                finaldict["SMA50"] = sma_50  
            elif i == "sma_200":
                finaldict["SMA200"] = sma_200  
            elif i == "volume":
                finaldict["Volume"] = volume  
            elif i == "change":
                finaldict["Change"] = change  
            elif i == "name":
                finaldict["name"] = name
            elif i == "industry":
                finaldict["industry"]= industry
            elif i == "all_info":
                finaldict = titleDict

        finalRestV2 = json.dumps({ 'data': finaldict})

    return HttpResponse(finalRestV2, content_type='text/json')
