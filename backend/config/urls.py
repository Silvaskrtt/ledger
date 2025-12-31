"""
URL configuration for config project.

URLs are organized by app, each app has its own urls.py file.
All API routes are prefixed with /api/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # URLs do allauth
    
    # API Routes — cada app gerencia suas próprias rotas
    #path('api/', include('home.urls')),
    path('api/', include('transactions.urls_api')),
    path('api/', include('accounts.urls')),
    path('api/', include('categories.urls')),
    path('api/', include('budgets.urls')),
    path('api/', include('payments.urls')),
    path('api/', include('tags.urls')),
    path('api/', include('recurrence.urls')),
    path('api/', include('goals.urls')),
    
    # Web
    path('', include('transactions.urls_web')),
    path('', include('users.urls_web')),
    path('', include('home.urls_web')),
]