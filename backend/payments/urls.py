from django.urls import path
from .views import (
    PaymentMethodListCreateView, PaymentMethodDetailView,
    InstallmentPlanListCreateView, InstallmentPlanDetailView
)

urlpatterns = [
    path('payment-methods/', PaymentMethodListCreateView.as_view(), name='payment-method-list'),
    path('payment-methods/<int:pk>/', PaymentMethodDetailView.as_view(), name='payment-method-detail'),
    
    path('installment-plans/', InstallmentPlanListCreateView.as_view(), name='installment-plan-list'),
    path('installment-plans/<int:pk>/', InstallmentPlanDetailView.as_view(), name='installment-plan-detail'),
]
