from django.urls import path
from .views import (
    TransactionListCreateView,
    TransactionDetailView,
    TransactionAccountListCreateView,
    TransactionAccountDetailView,
    TransactionTagListCreateView,
    TransactionTagDetailView,
)

urlpatterns = [
    # Transactions (API)
    path("transactions/", TransactionListCreateView.as_view(), name="api-transaction-list"),
    path("transactions/<int:pk>/", TransactionDetailView.as_view(), name="api-transaction-detail"),

    # Transaction Accounts
    path("transaction-accounts/", TransactionAccountListCreateView.as_view(), name="api-transaction-account-list"),
    path("transaction-accounts/<int:pk>/", TransactionAccountDetailView.as_view(), name="api-transaction-account-detail"),

    # Transaction Tags
    path("transaction-tags/", TransactionTagListCreateView.as_view(), name="api-transaction-tag-list"),
    path("transaction-tags/<int:pk>/", TransactionTagDetailView.as_view(), name="api-transaction-tag-detail"),
]