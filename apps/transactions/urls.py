from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('api/transactions/', views.api_transactions, name='api_transactions'),
    path('api/transactions/create/', views.api_transactions_create, name='api_transactions_create'),
    path('api/transactions/<int:pk>/update/', views.api_transactions_update, name='api_transactions_update'),
    path('api/transactions/<int:pk>/delete/', views.api_transactions_delete, name='api_transactions_delete'),
]   