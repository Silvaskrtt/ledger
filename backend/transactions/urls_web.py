# backend/transactions/urls_web.py

from django.urls import path
from .views import (
    TransactionManagerView,
)

urlpatterns = [
    # HTML views
    path("transactions/", TransactionManagerView.as_view(), name="transaction-manager"),
]