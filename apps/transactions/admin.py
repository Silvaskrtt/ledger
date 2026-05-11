from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'description', 'amount', 'type', 'category', 'date')
    list_filter = ('user', 'type', 'category', 'date')
    search_fields = ('description', 'user__username', 'category')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'type', 'category', 'amount', 'description', 'date')
        }),
        ('Informações Adicionais', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )