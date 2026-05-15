# import_export/urls.py
from django.urls import path
from . import views

app_name = 'import_export'

urlpatterns = [
    # Página principal
    path('', views.import_export_page, name='import_export_page'),
    
    # API Endpoints
    path('api/export/', views.api_export, name='api_export'),
    path('api/import/', views.api_import, name='api_import'),
    path('api/export/history/', views.api_export_history, name='api_export_history'),
    path('api/import/history/', views.api_import_history, name='api_import_history'),
    path('api/clear-data/', views.api_clear_all_data, name='api_clear_data'),
]