# config/__init__.py
"""
Patch para evitar conflito de registro duplicado do User.
"""

import django
from django.apps import AppConfig

class PatchConfig(AppConfig):
    name = 'config'
    
    def ready(self):
        # Import aqui para evitar import circular
        import django.contrib.admin.sites
        from django.contrib import admin
        from django.contrib.auth.models import User
        
        # Tenta desregistrar o User padrão se já estiver registrado
        try:
            admin.site.unregister(User)
            print("✓ User padrão desregistrado do admin")
        except admin.sites.NotRegistered:
            # Se não estiver registrado, não faz nada
            pass