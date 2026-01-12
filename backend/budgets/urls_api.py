# backend/budget/urls_api.py
from django.urls import path
from .views import (
    BudgetListCreateView, BudgetDetailView,
    BudgetCategoryLimitListCreateView, BudgetCategoryLimitDetailView,
    BudgetOverviewAPIView, create_budget_limit
)

urlpatterns = [
    path('budget-overview/', BudgetOverviewAPIView.as_view(), name='budget-overview'),
    path('budgets/', BudgetListCreateView.as_view(), name='budget-list'),
    path('budgets/<uuid:budget>/', BudgetDetailView.as_view(), name='budget-detail'),
    
    path('budget-category-limits/', BudgetCategoryLimitListCreateView.as_view(), name='budget-category-limit-list'),
    path('budget-category-limits/<int:pk>/', BudgetCategoryLimitDetailView.as_view(), name='budget-category-limit-detail'),
    
    path('create-budget-limit/', create_budget_limit, name='create-budget-limit'),
]