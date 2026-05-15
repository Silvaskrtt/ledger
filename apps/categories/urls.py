# categories/urls.py
from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    # Página principal
    path('', views.categories_page, name='categories_page'),
    
    # API Endpoints
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/categories/create/', views.api_categories_create, name='api_categories_create'),
    path('api/categories/<int:category_id>/update/', views.api_categories_update, name='api_categories_update'),
    path('api/categories/<int:category_id>/delete/', views.api_categories_delete, name='api_categories_delete'),
    path('api/categories/summary/', views.api_categories_summary, name='api_categories_summary'),
]