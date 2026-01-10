# backend/categories/urls_web.py

from django.urls import path
from .views import categories_management_view

urlpatterns = [
    path('managementCategories/', categories_management_view, name='management-categories'),
]
