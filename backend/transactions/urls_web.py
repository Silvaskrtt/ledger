# backend/transactions/urls_web.py

from django.urls import path
from .views import (
    CreateTransactionView,
    TransactionListView,
)

urlpatterns = [
    # HTML views
    path("transactions/new/", CreateTransactionView.as_view(), name="create-transaction-form"),
    path("transactions/list/", TransactionListView.as_view(), name="transaction-history"),
]
