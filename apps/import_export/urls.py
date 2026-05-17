# import_export/urls.py
from django.urls import path
from . import views

app_name = 'import_export'

urlpatterns = [
    # Página principal
    path('', views.import_export_page, name='import_export_page'),
    
    # API Endpoints - Exportação
    path('api/export/', views.api_export, name='api_export'),
    path('api/export/history/', views.api_export_history, name='api_export_history'),
    
    # API Endpoints - Importação
    path('api/import/', views.api_import, name='api_import'),
    path('api/import/history/', views.api_import_history, name='api_import_history'),
    path('api/import/<int:import_id>/detail/', views.api_import_detail, name='api_import_detail'),
    path('api/import/banks-formats/', views.api_import_banks_formats, name='api_import_banks_formats'),
    
    # Utilitários
    path('api/clear-data/', views.api_clear_all_data, name='api_clear_data'),
    path('api/import-debug/', views.api_import_debug, name='api_import_debug'),
]