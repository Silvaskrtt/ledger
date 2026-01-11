# backend/recurrence/serializers.py

from rest_framework import serializers
from .models import RecurrenceRule


class RecurrenceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrenceRule
        fields = ['recurrence_rule', 'user', 'category', 'payment_method', 'account', 'frequency', 'next_execution', 'max_executions', 'executions_count', 'amount', 'direction']
        read_only_fields = ['recurrence_rule', 'executions_count']
