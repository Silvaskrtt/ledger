# backend/goals/serializers.py

from rest_framework import serializers
from datetime import date
from .models import FinancialGoal

class FinancialGoalSerializer(serializers.ModelSerializer):
    percent = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = FinancialGoal
        fields = [
            'financial_goal',
            'name',
            'target_amount',
            'current_amount',
            'deadline',
            'strategy',
            'status',
            'percent'
        ]

    def validate_current_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Valor acumulado não pode ser negativo."
            )
        return value

    def validate_deadline(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                "Deadline deve ser uma data futura."
            )
        return value
