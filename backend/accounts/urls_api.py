# backend/accounts/urls_api.py

from django.urls import path
from .views import (
    AccountListCreateView, 
    AccountDetailView,
    CreditCardListCreateView,
    CreditCardDetailView,
    check_balance_consistency,
    sync_account_balances,
)

urlpatterns = [
    # API endpoints
    path('accounts/check-consistency/', check_balance_consistency, name='check-balance-consistency'),
    path('accounts/sync-balances/', sync_account_balances, name='sync-balances'),
    path('accounts/', AccountListCreateView.as_view(), name='account-list'),
    path('accounts/<uuid:pk>/', AccountDetailView.as_view(), name='account-detail'),
    
    path('credit-cards/', CreditCardListCreateView.as_view(), name='credit-card-list'),
    path('credit-cards/<uuid:pk>/', CreditCardDetailView.as_view(), name='credit-card-detail'),
]