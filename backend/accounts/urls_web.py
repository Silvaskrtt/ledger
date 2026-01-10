# backend/accounts/web_urls.py

from django.urls import path
from .views import credit_cards_view, account_management_view

urlpatterns = [
    path('cartoes/', credit_cards_view, name='credit-cards'),
    path('management/', account_management_view, name='account-management'),
]