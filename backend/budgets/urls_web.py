# backend/budget/urls_web.py

from django.urls import path
from .views import (
    budget_view
)

urlpatterns = [
    path("budget/", budget_view, name="budget")
]
