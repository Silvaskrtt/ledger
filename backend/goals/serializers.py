# backend/goals/serializers.py
from rest_framework import serializers
from datetime import date
from .models import FinancialGoal

class FinancialGoalSerializer(serializers.ModelSerializer):
    percent = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
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
            'percent',
            'created_at'
        ]
        read_only_fields = ['financial_goal', 'created_at', 'status', 'percent']

    def get_percent(self, obj):
        return obj.percent

    def get_status(self, obj):
        return obj.status

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
    
    def validate(self, data):
        # Validar que current_amount não pode ser maior que target_amount
        current_amount = data.get('current_amount', 0)
        target_amount = data.get('target_amount')
        
        if target_amount and current_amount > target_amount:
            raise serializers.ValidationError({
                'current_amount': 'Valor atual não pode ser maior que o valor alvo.'
            })
        
        return data

    def create(self, validated_data):
        # Garantir que user é setado
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)