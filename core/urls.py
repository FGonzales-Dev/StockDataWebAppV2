from xml.etree.ElementInclude import include
from django.urls import path
from core import views_firestore

urlpatterns = [
    path('', views_firestore.scrape_firestore, name='stockData'),
    path('api/stock/<str:ticker>/<str:market>/<str:data_type_param>/', views_firestore.api_stock_data_firestore, name='api_stock_data_firestore'),
]
