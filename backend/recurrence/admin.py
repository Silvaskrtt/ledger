from django.contrib import admin
from .models import RecurrenceRule


@admin.register(RecurrenceRule)
class RecurrenceRuleAdmin(admin.ModelAdmin):
    list_display = ('id_recurrence_rule', 'frequency', 'next_execution', 'max_executions', 'executions_count', 'amount', 'direction', 'id_user', 'id_category', 'id_payment_method', 'id_account')
    search_fields = ('id_recurrence_rule',)
