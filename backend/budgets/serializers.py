from rest_framework import serializers
from .models import Budget, BudgetCategoryLimit


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id_budget', 'id_user', 'period_type', 'period_start']
        read_only_fields = ['id_budget']


class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetCategoryLimit
        fields = ['id_budget', 'id_category', 'limit_amount']
