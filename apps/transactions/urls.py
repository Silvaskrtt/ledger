from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('add/', views.TransactionCreateView.as_view(), name='transaction_add'),
    path('api/transactions/', views.api_transactions, name='api_transactions'),  # API endpoint
]
