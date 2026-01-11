from django.contrib import admin
from .models import RecurrenceRule


@admin.register(RecurrenceRule)
class RecurrenceRuleAdmin(admin.ModelAdmin):
    list_display = ('recurrence_rule', 'frequency', 'next_execution', 'max_executions', 'executions_count', 'amount', 'direction', 'user', 'category', 'payment_method', 'account')
    search_fields = ('recurrence_rule',)
