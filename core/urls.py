from xml.etree.ElementInclude import include
from django.urls import path
from core import scraperVersionTwo, views_optimized, views_firestore

urlpatterns = [

    # EXISTING URLs (using optimized tasks behind the scenes)
    # path('', scraperVersionTwo.scrape, name='stockData'),
    path('stockDataDownload', scraperVersionTwo.download, name='stockDataDownload'),
    path('get_task_info/', scraperVersionTwo.get_task_info, name='get_task_info'),

    # OPTIMIZED URLs (optional - for direct optimized access)
    path('optimized/', views_optimized.scrape_optimized, name='stockData_optimized'),
    path('optimized/get_task_info/', views_optimized.get_task_info_optimized, name='get_task_info_optimized'),
    path('optimized/direct/', views_optimized.direct_scrape_optimized, name='direct_scrape_optimized'),

    # NEW FIRESTORE URLs (check-first approach with Firestore storage)
    path('', views_firestore.scrape_firestore, name='stockData'),
    path('firestore/get_task_info/', views_firestore.get_task_info_firestore, name='get_task_info_firestore'),
    path('firestore/check_status/', views_firestore.check_data_status_firestore, name='check_data_status_firestore'),
    path('firestore/storage_stats/', views_firestore.storage_stats_firestore, name='storage_stats_firestore'),
    path('firestore/direct/', views_firestore.direct_scrape_firestore, name='direct_scrape_firestore'),

    # DEPRECATED TO DELETE SOON
    # path('scrape', historicalData.scrape, name='scrape'),
    # path('valuation', historicalData.scrape_valuation, name='valuation'),
    # path('dividends', historicalData.scrape_dividends, name='dividends'),
    # path('performance', historicalData.scrape_operating_performance, name='performance'),
    # path('stock_history_all', historicalData.stock_history_all, name='home'),
    # path('stock_history_key_ratio', historicalData.stock_history_key_ratio, name='home'),
    # path('stock/<data_param>/', views.home, name='home'),
    # path('history', views.stockhistory, name='home'),
    # path('income_statement', views.stock_income_statement, name='home'),
    # path('cash_flow', views.stock_cash_flow, name='home'),
    # path('stock_history_key_ratio_json', historicalData.stock_history_key_ratio_json, name='home'),
    # path('stock_history_json', historicalData.stock_history_json, name='home'),
]

#http://127.0.0.1:8000/stock_history_json?ticker=aapl&market=XNAS&type=is

# NEW FIRESTORE ENDPOINTS:
# http://127.0.0.1:8000/firestore/ - Main Firestore scraping interface
# http://127.0.0.1:8000/firestore/check_status/?ticker=AAPL&market=XNAS - Check what data exists
# http://127.0.0.1:8000/firestore/storage_stats/ - Get storage statistics
# http://127.0.0.1:8000/firestore/direct/ - Direct scraping API endpoint