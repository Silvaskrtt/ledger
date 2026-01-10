# backend/accounts/serializers.py

from rest_framework import serializers
from .models import Account

class CreditCardSerializer(serializers.ModelSerializer):
    is_credit_card = serializers.BooleanField(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    available_credit = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id_account', 'name', 'type', 'type_display', 'initial_balance', 'balance',
            'bank_name', 'description', 'credit_limit', 'closing_day', 'due_day',
            'icon', 'color', 'is_active', 'created_at', 'updated_at',
            'is_credit_card', 'available_credit', 'user'
        ]
        read_only_fields = [
            'id_account', 'created_at', 'updated_at', 
            'is_credit_card', 'balance', 'user'
        ]
    
    def get_available_credit(self, obj):
        return obj.available_credit
    
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
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    available_credit = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id_account', 'name', 'type', 'type_display', 'initial_balance', 'balance',
            'bank_name', 'description', 'credit_limit', 'closing_day', 'due_day',
            'icon', 'color', 'is_active', 'created_at', 'updated_at',
            'is_credit_card', 'available_credit', 'user'
        ]
        read_only_fields = [
            'id_account', 'created_at', 'updated_at', 
            'is_credit_card', 'balance', 'user'
        ]
    
    def get_available_credit(self, obj):
        return obj.available_credit
    
    def validate(self, data):
        # Validações específicas para cartões de crédito
        if data.get('type') == 'CREDIT_CARD':
            if not data.get('credit_limit') or data['credit_limit'] <= 0:
                raise serializers.ValidationError({
                    'credit_limit': 'Limite de crédito é obrigatório e deve ser maior que zero para cartões.'
                })
            if not data.get('closing_day'):
                raise serializers.ValidationError({
                    'closing_day': 'Dia de fechamento é obrigatório para cartões de crédito.'
                })
            if not data.get('due_day'):
                raise serializers.ValidationError({
                    'due_day': 'Dia de vencimento é obrigatório para cartões de crédito.'
                })
        
        # Valida dia do fechamento e vencimento
        if data.get('closing_day') and (data['closing_day'] < 1 or data['closing_day'] > 31):
            raise serializers.ValidationError({
                'closing_day': 'Dia do fechamento deve estar entre 1 e 31.'
            })
        
        if data.get('due_day') and (data['due_day'] < 1 or data['due_day'] > 31):
            raise serializers.ValidationError({
                'due_day': 'Dia do vencimento deve estar entre 1 e 31.'
            })
        
        return data
    
    def create(self, validated_data):
        # Garante que o usuário seja o usuário autenticado
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)