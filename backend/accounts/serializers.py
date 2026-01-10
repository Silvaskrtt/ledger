# backend/accounts/serializers.py

from rest_framework import serializers
from .models import Account

class CreditCardSerializer(serializers.ModelSerializer):
    is_credit_card = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id_account', 'name', 'bank_name', 'credit_limit',
            'closing_day', 'due_day', 'type', 'balance',
            'created_at', 'is_credit_card'
        ]
        read_only_fields = ['id_account', 'created_at', 'is_credit_card']
    
    def validate(self, data):
        # Define type como CREDIT_CARD
        data['type'] = 'CREDIT_CARD'
            
        # Agora valida os campos obrigatórios
        if not data.get('bank_name'):
            raise serializers.ValidationError(
                {'bank_name': 'Banco é obrigatório para cartões de crédito.'}
            )
        if not data.get('closing_day'):
            raise serializers.ValidationError(
                {'closing_day': 'Dia de fechamento é obrigatório para cartões de crédito.'}
            )
        if not data.get('due_day'):
            raise serializers.ValidationError(
                {'due_day': 'Dia de vencimento é obrigatório para cartões de crédito.'}
            )
            
        return data

class AccountSerializer(serializers.ModelSerializer):
    is_credit_card = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id_account', 'name', 'bank_name', 'credit_limit',
            'closing_day', 'due_day', 'type', 'balance',
            'created_at', 'is_credit_card', 'user'
        ]
        read_only_fields = ['id_account', 'created_at', 'is_credit_card', 'user']