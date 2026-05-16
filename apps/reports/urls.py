# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Página principal
    path('', views.reports_page, name='reports_page'),
    
    # API Endpoints
    path('api/summary/', views.api_report_summary, name='api_summary'),
    path('api/monthly-trend/', views.api_monthly_trend, name='api_monthly_trend'),
    path('api/expenses-by-category/', views.api_expenses_by_category, name='api_expenses_by_category'),
    path('api/top-expenses/', views.api_top_expenses, name='api_top_expenses'),
    path('api/monthly-summary/', views.api_monthly_summary, name='api_monthly_summary'),
    path('api/export/', views.api_export_report, name='api_export'),
]