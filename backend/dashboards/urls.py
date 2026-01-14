# backend/dashboards/urls.py

from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    # Dashboard de gastos por cartão
    path('dashboard/card-expenses/', views.card_expenses_dashboard, name='card-expenses'),
    
    # Dashboard de gastos por categoria
    path('dashboard/category-expenses/', views.category_expenses_dashboard, name='category-expenses'),
    
    # Dashboard de fluxo de caixa
    path('dashboard/cash-flow/', views.cash_flow_dashboard, name='cash-flow'),
]
