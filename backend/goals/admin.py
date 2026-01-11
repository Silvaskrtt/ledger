from django.contrib import admin
from .models import FinancialGoal


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('financial_goal', 'target_amount', 'deadline', 'strategy', 'status', 'user')
    search_fields = ('user__email',)
