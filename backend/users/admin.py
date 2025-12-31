from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone']
    search_fields = ['user__email', 'user__username', 'phone']
    
# NÃO registre User aqui - Allauth/Django já cuida disso
