from django.urls import path
from . import views

app_name = 'dash_calendar'

urlpatterns = [
    path('', views.calendar_page, name='calendar_page'),
    path('api/transactions/', views.api_transactions, name='api_transactions'),
    path('api/transactions/create/', views.api_transactions_create, name='api_transactions_create'),
    path('api/transactions/<int:pk>/update/', views.api_transactions_update, name='api_transactions_update'),
    path('api/transactions/<int:pk>/delete/', views.api_transactions_delete, name='api_transactions_delete'),
    path('api/transactions/monthly-summary/', views.api_monthly_summary, name='api_monthly_summary'),
    path('api/transactions/balance/', views.api_monthly_balance, name='api_monthly_balance'),
    path('api/transactions/filter/', views.api_transactions_filter, name='api_transactions_filter'),
]
