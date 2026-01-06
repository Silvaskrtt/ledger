from django.urls import path
from .views_web import goals_page

app_name = "goals"

urlpatterns = [
    path("goals/", goals_page, name="financial-goals-page"),
]
