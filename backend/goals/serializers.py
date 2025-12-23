from rest_framework import serializers
from .models import FinancialGoal


class FinancialGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialGoal
        fields = ['id_financial_goal', 'id_user', 'name', 'target_amount', 'deadline', 'strategy', 'status']
        read_only_fields = ['id_financial_goal']
