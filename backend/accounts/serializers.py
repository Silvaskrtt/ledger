# backend/accounts/serializers.py
from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id_account', 'type', 'active', 'id_user']
        read_only_fields = ['id_account']

class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            'id_account', 'name', 'bank_name', 'credit_limit', 
            'closing_day', 'due_day', 'type', 'created_at'
        ]
        read_only_fields = ['type', 'created_at']