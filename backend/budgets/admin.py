from django.contrib import admin
from .models import Budget, BudgetCategoryLimit


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('id_budget', 'period_type', 'period_start', 'id_user')
    search_fields = ('id_budget',)


@admin.register(BudgetCategoryLimit)
class BudgetCategoryLimitAdmin(admin.ModelAdmin):
    list_display = ('id_budget', 'id_category', 'limit_amount')
    search_fields = ('id_budget__id_budget',)
