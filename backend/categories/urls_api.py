# backend/categories/urls_api.py

from django.urls import path
from .views import CategoryListCreateView, CategoryDetailView, categories_management_view


urlpatterns = [
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
]
