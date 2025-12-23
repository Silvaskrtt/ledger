from rest_framework import serializers
from .models import RecurrenceRule


class RecurrenceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrenceRule
        fields = ['id_recurrence_rule', 'id_user', 'id_category', 'id_payment_method', 'id_account', 'frequency', 'next_execution', 'max_executions', 'executions_count', 'amount', 'direction']
        read_only_fields = ['id_recurrence_rule', 'executions_count']
