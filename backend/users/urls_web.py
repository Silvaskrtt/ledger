# users/urls_web.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Página inicial após login
    path('profile/', views.profile_view, name='profile'),
]