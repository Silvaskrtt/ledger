# backend/categories/admin.py

from django.contrib import admin
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'parent_category', 'user', 'created_at')
    list_filter = ('type', 'user', 'parent_category')
    search_fields = ('name', 'user__username')
    readonly_fields = ('category', 'created_at', 'updated_at')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'type', 'icon', 'color')
        }),
        ('Hierarquia', {
            'fields': ('parent_category', 'user')
        }),
        ('Metadados', {
            'fields': ('category', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )