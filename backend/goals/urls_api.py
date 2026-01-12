# backend/goals/urls_api.py
from django.urls import path
from .views import FinancialGoalListCreateView, FinancialGoalDetailView

urlpatterns = [
    path('financial-goals/', FinancialGoalListCreateView.as_view(), name='financial-goal-list'),
    path('financial-goals/<uuid:pk>/', FinancialGoalDetailView.as_view(), name='financial-goal-detail'),
]