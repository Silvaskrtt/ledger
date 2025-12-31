# serializers.py
from rest_framework import serializers
from .models import Transaction, TransactionAccount, TransactionTag
from django.utils import timezone

class TransactionCreateSerializer(serializers.ModelSerializer):
    id_account = serializers.IntegerField(write_only=True)
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )

    class Meta:
        model = Transaction
        fields = [
            'id_category',
            'id_payment_method',
            'amount',
            'direction',
            'currency',
            'origin',    
            'occurred_at',
            'id_account',
            'tags'
        ]
        read_only_fields = ['id_user']  # Será definido na view
    
    def validate_direction(self, value):
        if value not in ['IN', 'OUT']:
            raise serializers.ValidationError("Direção inválida. Use 'IN' ou 'OUT'.")
        return value
    
    def validate_occurred_at(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("Data futura não permitida.")
        return value
    
    def validate_origin(self, value):
        valid_origins = ['MANUAL', 'RECURRENT', 'INSTALLMENT']
        if value not in valid_origins:
            raise serializers.ValidationError(f"Origem inválida. Use: {', '.join(valid_origins)}")
        return value
    
    def validate_currency(self, value):
        valid_currencies = ['BRL', 'USD', 'EUR']
        if value not in valid_currencies:
            raise serializers.ValidationError(f"Moeda inválida. Use: {', '.join(valid_currencies)}")
        return value
    
    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError({"amount": "O valor deve ser maior que zero."})
        return data

class TransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id_category', 'id_payment_method', 'amount', 'direction', 'occurred_at']

class TransactionAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionAccount
        fields = ['id_transaction', 'id_account', 'role']

class TransactionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionTag
        fields = ['id_transaction', 'id_tag']