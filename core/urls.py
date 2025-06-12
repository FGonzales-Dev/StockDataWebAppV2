from xml.etree.ElementInclude import include
from django.urls import path
from django.views.generic import TemplateView
from core import historicalData, scraperVersionTwo, views, monitoring_views

urlpatterns = [

    # (TO BE DEPRECATED)
    # path('stock/<data_param>/', views.home, name='home'),
    # path('history', views.stockhistory, name='home'),
    # path('income_statement', views.stock_income_statement, name='home'),
    # path('cash_flow', views.stock_cash_flow, name='home'),

    #JSON FOR GOOGLESHEET (TO BE DEPRECATED)
    # path('scrape', historicalData.scrape, name='scrape'),
    # path('valuation', historicalData.scrape_valuation, name='valuation'),
    # path('dividends', historicalData.scrape_dividends, name='dividends'),
    # path('performance', historicalData.scrape_operating_performance, name='performance'),
    # path('stock_history_all', historicalData.stock_history_all, name='home'),
    # path('stock_history_key_ratio', historicalData.stock_history_key_ratio, name='home'),

    #JSON FOR GOOGLESHEET (TO BE DEPRECATED)
    # path('stock_history_key_ratio_json', historicalData.stock_history_key_ratio_json, name='home'),

    ######TEST FOR JSON#######
    # path('stock_history_json', historicalData.stock_history_json, name='home'),



    # New financial statements JSON endpoint (Open Access)
    path('financial-statements-json', scraperVersionTwo.financial_statements_json, name='financial_statements_json'),
    path('', scraperVersionTwo.scrape, name='stockData'),
    path('stockDataDownload', scraperVersionTwo.download, name='stockDataDownload'),
    path('get_task_info/', scraperVersionTwo.get_task_info, name='get_task_info'),
 
    # Resource monitoring endpoints
    path('monitoring/system-status/', monitoring_views.system_status, name='system_status'),
    path('monitoring/history/', monitoring_views.resource_usage_history, name='resource_usage_history'),
    path('monitoring/alerts/', monitoring_views.resource_alerts, name='resource_alerts'),
    path('monitoring/dashboard/', TemplateView.as_view(template_name='monitoring_dashboard.html'), name='monitoring_dashboard'),

]


#http://127.0.0.1:8000/stock_history_json?ticker=aapl&market=XNAS&type=is