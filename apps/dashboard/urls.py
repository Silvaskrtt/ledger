from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # API Endpoints
    path('api/summary/', views.dashboard_summary, name='api_summary'),
    path('api/monthly-trend/', views.dashboard_monthly_trend, name='api_monthly_trend'),
    path('api/expenses-by-category/', views.dashboard_expenses_by_category, name='api_expenses_by_category'),
    path('api/recent-transactions/', views.dashboard_recent_transactions, name='api_recent_transactions'),
    
    # Template View (fallback)
    path('', views.dashboard_context_view, name='dashboard'),
]
