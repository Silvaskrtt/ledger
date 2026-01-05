# backend/budgets/serializers.py

from rest_framework import serializers
from .models import Budget, BudgetCategoryLimit
from rest_framework.permissions import IsAuthenticated
from .services import get_or_create_current_month_budget

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id_budget', 'id_user', 'period_type', 'period_start']
        read_only_fields = ['id_budget']


class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetCategoryLimit
        fields = ['id', 'id_category', 'limit_amount']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")

        budget = get_or_create_current_month_budget(request.user)

        return BudgetCategoryLimit.objects.create(
            id_budget=budget,
            **validated_data
        )