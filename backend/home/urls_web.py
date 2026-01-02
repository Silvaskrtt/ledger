# backend/home/urls_web.py
from django.urls import path
from .views import (teste_html_view,)

urlpatterns = [
    #HOME
    path("teste-html/", teste_html_view, name="teste_html")
]