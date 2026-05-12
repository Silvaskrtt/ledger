from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/categories/create/', views.api_categories_create, name='api_categories_create'),
]