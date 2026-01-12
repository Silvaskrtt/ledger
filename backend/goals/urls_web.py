# backend/goals/urls_web.py

from django.urls import path, include
from .views import goals_page

app_name = "goals"

urlpatterns = [
    path("goals/", goals_page, name="financial-goals-page"),
    path("api/goals/", include('goals.urls_api')),  # Note o prefixo 'api/goals/'
]