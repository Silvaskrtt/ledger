from django.contrib import admin
from .models import recurrence_rules


@admin.register(recurrence_rules)
class recurrenceRulesAdmin(admin.ModelAdmin):
    list_display = ('id_recurrence_rule', 'frequency', 'next_execution', 'max_executions', 'executions_count', 'amount', 'direction', 'id_user', 'id_category', 'id_payment_method', 'id_account')
    search_fields = ('id_recurrence_rule',)
