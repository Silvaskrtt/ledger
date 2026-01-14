# backend/dashboards/serializers.py

from rest_framework import serializers


class CardExpenseDataSerializer(serializers.Serializer):
    """Serializer para dados de gastos por cartão"""
    card_name = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=14, decimal_places=2)
    transaction_count = serializers.IntegerField()


class CategoryExpenseDataSerializer(serializers.Serializer):
    """Serializer para dados de gastos por categoria"""
    category_name = serializers.CharField()
    category_id = serializers.CharField()
    category_color = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=14, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    transaction_count = serializers.IntegerField()


class CashFlowDataSerializer(serializers.Serializer):
    """Serializer para dados de fluxo de caixa"""
    month = serializers.CharField()
    income = serializers.DecimalField(max_digits=14, decimal_places=2)
    expense = serializers.DecimalField(max_digits=14, decimal_places=2)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)


class DashboardResponseSerializer(serializers.Serializer):
    """Serializer genérico para resposta de dashboards"""
    data = serializers.ListField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    metadata = serializers.DictField(required=False)
