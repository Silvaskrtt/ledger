from django.urls import path
from .views import (
    CreateTransactionView, TransactionListCreateView, TransactionDetailView,
    TransactionAccountListCreateView, TransactionAccountDetailView,
    TransactionTagListCreateView, TransactionTagDetailView
)

urlpatterns = [
    # Transactions
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    
    # Template view para formulário HTML
    path('transactions/new/', CreateTransactionView.as_view(), name='create-transaction-form'),
    
    # Transaction Accounts
    path('transaction-accounts/', TransactionAccountListCreateView.as_view(), name='transaction-account-list'),
    path('transaction-accounts/<int:pk>/', TransactionAccountDetailView.as_view(), name='transaction-account-detail'),
    
    # Transaction Tags
    path('transaction-tags/', TransactionTagListCreateView.as_view(), name='transaction-tag-list'),
    path('transaction-tags/<int:pk>/', TransactionTagDetailView.as_view(), name='transaction-tag-detail'),
]
