# backend/dashboards/urls_web.py

from django.urls import path
from . import views_web

app_name = 'dashboards_web'

urlpatterns = [
    path('dashboards/', views_web.DashboardView.as_view(), name='dashboard'),
]
