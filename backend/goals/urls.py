from django.urls import path
from .views import FinancialGoalListCreateView, FinancialGoalDetailView

urlpatterns = [
    path('financial-goals/', FinancialGoalListCreateView.as_view(), name='financial-goal-list'),
    path('financial-goals/<int:pk>/', FinancialGoalDetailView.as_view(), name='financial-goal-detail'),
]
