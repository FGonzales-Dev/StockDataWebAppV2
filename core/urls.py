from xml.etree.ElementInclude import include
from django.urls import path
from core import views_firestore

urlpatterns = [
    # NEW FIRESTORE URLs (check-first approach with Firestore storage)
    path('', views_firestore.scrape_firestore, name='stockData'),
    path('firestore/get_task_info/', views_firestore.get_task_info_firestore, name='get_task_info_firestore'),
    path('firestore/check_status/', views_firestore.check_data_status_firestore, name='check_data_status_firestore'),
    path('firestore/storage_stats/', views_firestore.storage_stats_firestore, name='storage_stats_firestore'),
    path('firestore/direct/', views_firestore.direct_scrape_firestore, name='direct_scrape_firestore'),
]
