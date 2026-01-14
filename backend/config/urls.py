"""
URL configuration for config project.

Arquitetura:
- Rotas de API são centralizadas sob o prefixo /api/
- Cada app é responsável por expor suas próprias URLs
- Rotas Web (HTML) ficam separadas das rotas de API
"""
# backend/config/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # =====================================================
    # Admin
    # =====================================================
    path('admin/', admin.site.urls),

    # =====================================================
    # Autenticação (django-allauth)
    # =====================================================
    path('accounts/', include('allauth.urls')),  # Login, logout, signup, etc.

    # =====================================================
    # API (REST)
    # Cada app gerencia suas próprias rotas de API
    # Prefixo padrão: /api/
    # =====================================================

    path('api/', include('transactions.urls_api')),
    path('api/', include('accounts.urls_api')),
    path('api/', include('categories.urls_api')),
    path('api/', include('budgets.urls_api')),
    path('api/', include('payments.urls')),
    path('api/', include('tags.urls_api')),
    path('api/', include('recurrence.urls')),
    path('api/', include('goals.urls_api')),
    path('api/', include('dashboards.urls')),

    # =====================================================
    # Web (HTML / Server-side rendering)
    # =====================================================
    path('', include('transactions.urls_web')),
    path('', include('users.urls_web')),
    path('', include('home.urls_web')),
    path('', include('budgets.urls_web')),
    path('', include('goals.urls_web')),
    path('', include('accounts.urls_web')),
    path('', include('categories.urls_web')),
    path('', include('dashboards.urls_web')),
]
