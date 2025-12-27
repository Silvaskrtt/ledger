from django.urls import path
from .views import AccountListCreateView, AccountDetailView

urlpatterns = [
    path('accounts/', AccountListCreateView.as_view(), name='account-list'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
]
