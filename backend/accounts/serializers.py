# backend/accounts/serializers.py

from rest_framework import serializers
from decimal import Decimal
from .models import CreditCardBill, Account

class AccountSerializer(serializers.ModelSerializer):
    is_credit_card = serializers.BooleanField(read_only=True)
    available_credit = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'account', 'name', 'type', 'type_display', 'initial_balance', 'balance',
            'bank_name', 'description', 'credit_limit', 'closing_day', 'due_day',
            'icon', 'color', 'is_active', 'created_at', 'updated_at', 'user',
            'is_credit_card', 'available_credit'
        ]
        read_only_fields = [
            'account', 'created_at', 'updated_at', 'balance', 'user',
            'is_credit_card', 'available_credit'
        ]
    
    def validate(self, data):
        # Verificar se já existe uma conta com o mesmo nome para este usuário
        user = self.context['request'].user
        name = data.get('name')
        
        if name:
            # Se estiver editando (self.instance existe), excluir a própria conta da verificação
            if self.instance:
                existing = Account.objects.filter(
                    user=user, 
                    name=name
                ).exclude(account=self.instance.account).exists()
            else:
                existing = Account.objects.filter(user=user, name=name).exists()
            
            if existing:
                raise serializers.ValidationError({
                    'name': 'Você já tem uma conta com este nome.'
                })
        
        return data
    
    def get_available_credit(self, obj):
        """Método para calcular/serializar o available_credit."""
        if hasattr(obj, 'available_credit') and obj.available_credit is not None:
            # Retorna como float para JSON
            return float(obj.available_credit)
        return None
    
    def to_representation(self, instance):
        """
        Converte campos Decimal para float na serialização JSON.
        Isso evita o erro 'toFixed is not a function' no frontend.
        """
        representation = super().to_representation(instance)
        
        # Converter campos Decimal para float
        decimal_fields = ['balance', 'initial_balance', 'credit_limit']
        for field in decimal_fields:
            if field in representation and representation[field] is not None:
                try:
                    representation[field] = float(representation[field])
                except (ValueError, TypeError):
                    pass
        
        return representation
    
    def create(self, validated_data):
        # Garante que o usuário seja o usuário autenticado
        validated_data['user'] = self.context['request'].user
        
        # Define o saldo inicial
        initial_balance = validated_data.get('initial_balance', 0)
        validated_data['balance'] = initial_balance
        
        return super().create(validated_data)
    
    def validate_balance(self, value):
        """Impede modificação manual do saldo."""
        if self.instance and 'balance' in self.initial_data:
            raise serializers.ValidationError(
                "O saldo não pode ser modificado diretamente. "
                "Ele é calculado automaticamente a partir das transações."
            )
        return value
    
    def update(self, instance, validated_data):
        """Remove balance dos dados a serem atualizados."""
        validated_data.pop('balance', None)
        return super().update(instance, validated_data)
    
class CreditCardBillSerializer(serializers.ModelSerializer):
    credit_card_name = serializers.CharField(source='credit_card.name', read_only=True)
    pending_amount = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    due_date_formatted = serializers.SerializerMethodField()
    period_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CreditCardBill
        fields = [
            'id_bill',
            'credit_card',
            'credit_card_name',
            'start_date',
            'end_date',
            'due_date',
            'due_date_formatted',
            'period_formatted',
            'total_amount',
            'paid_amount',
            'pending_amount',
            'minimum_payment',
            'status',
            'status_display'
        ]
    
    def get_pending_amount(self, obj):
        """Calcula valor pendente"""
        return float(obj.total_amount - obj.paid_amount)
    
    def get_due_date_formatted(self, obj):
        """Formata data de vencimento"""
        return obj.due_date.strftime('%d/%m/%Y') if obj.due_date else ''
    
    def get_period_formatted(self, obj):
        """Retorna período formatado"""
        if obj.start_date and obj.end_date:
            return f"{obj.start_date.strftime('%d/%m')} - {obj.end_date.strftime('%d/%m/%Y')}"
        return ''

class CreditCardSerializer(AccountSerializer):
    """
    Serializer específico para cartões de crédito.
    Herda de AccountSerializer, então já inclui is_credit_card e available_credit.
    """
    is_credit_card = serializers.BooleanField(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    available_credit = serializers.SerializerMethodField()
    
    class Meta(AccountSerializer.Meta):
        # Herda todos os campos do AccountSerializer
        pass
    
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
