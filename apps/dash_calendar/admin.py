from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'amount', 'date', 'category', 'tag', 'recurrence']
    list_filter = ['type', 'category', 'recurrence', 'date']
    search_fields = ['description', 'category', 'tag']
    ordering = ['-date', '-created_at']
