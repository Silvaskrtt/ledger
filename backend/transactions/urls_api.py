from django.urls import path

from .views import (
    TransactionListCreateView,
    TransactionDetailView,
    TransactionAccountListCreateView,
    TransactionAccountDetailView,
    TransactionTagListCreateView,
    TransactionTagDetailView,
    get_transaction_form,
    simple_debug_view,
)

urlpatterns = [
    # Transactions (API)
    path("transactions/", TransactionListCreateView.as_view(), name="api-transaction-list"),
    path("transactions/<uuid:pk>/", TransactionDetailView.as_view(), name="api-transaction-detail"),
    
    # Forms (HTML para modais)
    path("transactions/form/", get_transaction_form, name="api-transaction-form"),
    path("transactions/<uuid:transaction_id>/form/", get_transaction_form, name="api-transaction-edit-form"),

    # Transaction Accounts
    path("transaction-accounts/", TransactionAccountListCreateView.as_view(), name="api-transaction-account-list"),
    path("transaction-accounts/<int:pk>/", TransactionAccountDetailView.as_view(), name="api-transaction-account-detail"),

    # Transaction Tags
    path("transaction-tags/", TransactionTagListCreateView.as_view(), name="api-transaction-tag-list"),
    path("transaction-tags/<int:pk>/", TransactionTagDetailView.as_view(), name="api-transaction-tag-detail"),
    
    path('simple-debug/', simple_debug_view, name='api-transaction-simple-debug'),
]