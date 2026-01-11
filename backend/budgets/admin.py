from django.contrib import admin
from .models import Budget, BudgetCategoryLimit


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('budget', 'period_type', 'period_start', 'user')
    search_fields = ('budget',)


@admin.register(BudgetCategoryLimit)
class BudgetCategoryLimitAdmin(admin.ModelAdmin):
    list_display = ('budget', 'category', 'limit_amount')
    search_fields = ('budget__budget',)
