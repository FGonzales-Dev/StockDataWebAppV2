from django.urls import path
from register import  views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path("login/", views.login_request, name="login")
]