from django.contrib import admin
from .models import Transaction, MonthlyBudget


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'amount', 'date', 'category', 'tag', 'recurrence']
    list_filter = ['type', 'category', 'recurrence', 'date']
    search_fields = ['description', 'category', 'tag']
    ordering = ['-date', '-created_at']


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'month', 'year', 'total_planned', 'divisor']
    list_filter = ['year', 'month']
    search_fields = ['user__username']
    ordering = ['-year', '-month']