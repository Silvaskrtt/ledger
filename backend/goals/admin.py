from django.contrib import admin
from .models import FinancialGoal


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('id_financial_goal', 'target_amount', 'deadline', 'strategy', 'status', 'id_user')
    search_fields = ('id_user__email',)
