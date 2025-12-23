from django.contrib import admin
from .models import budgets, budget_categories_limits


@admin.register(budgets)
class budgetAdmin(admin.ModelAdmin):
    list_display = ('id_budget', 'period_type', 'period_start', 'id_user')
    search_fields = ('id_budget',)


@admin.register(budget_categories_limits)
class budgetCategoryLimitsAdmin(admin.ModelAdmin):
    list_display = ('id_budget', 'limit_amount', 'id_budget', 'id_category')
    search_fields = ('id_budget_category_limit',)
