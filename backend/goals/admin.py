from django.contrib import admin
from .models import financial_goals


@admin.register(financial_goals)
class financialGoalsAdmin(admin.ModelAdmin):
    list_display = ('id_financial_goal', 'target_amount', 'deadline', 'strategy', 'status', 'id_user')
    search_fields = ('name',)
