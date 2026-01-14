# backend/accounts/urls_api.py

from django.urls import path
from .views import (
    AccountListCreateView, 
    AccountDetailView,
    CreditCardListCreateView,
    CreditCardDetailView,
    check_balance_consistency,
    sync_account_balances,
    get_credit_card_bills, 
    pay_credit_card_bill, 
    get_payment_accounts,
)

urlpatterns = [
    # =====================================================
    # API endpoints para Contas
    # =====================================================
    path('accounts/check-consistency/', check_balance_consistency, name='check-balance-consistency'),
    path('accounts/sync-balances/', sync_account_balances, name='sync-balances'),
    path('accounts/', AccountListCreateView.as_view(), name='account-list'),
    path('accounts/<uuid:pk>/', AccountDetailView.as_view(), name='account-detail'),
    
    # =====================================================
    # API endpoints para Cartões de Crédito
    # =====================================================
    path('credit-cards/', CreditCardListCreateView.as_view(), name='credit-card-list'),
    path('credit-cards/<uuid:pk>/', CreditCardDetailView.as_view(), name='credit-card-detail'),
    
    # =====================================================
    # API endpoints para Faturas e Pagamentos
    # =====================================================
    path('credit-cards/<uuid:card_id>/bills/', get_credit_card_bills, name='credit-card-bills'),
    path('credit-cards/pay-bill/', pay_credit_card_bill, name='pay-credit-card-bill'),
    path('accounts/payment-accounts/', get_payment_accounts, name='payment-accounts'),
]