from django.urls import path
from .views import AccountListCreateView, AccountDetailView

from .views import credit_cards_view

urlpatterns = [
    path('accounts/', AccountListCreateView.as_view(), name='account-list'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
    
    path('cartoes/', credit_cards_view, name='credit-cards'),
]
