# serializers.py
from rest_framework import serializers
from .models import Transaction, TransactionAccount, TransactionTag
from django.utils import timezone
from categories.models import Category
from payments.models import PaymentMethod
from accounts.models import Account
from tags.models import Tag

class TransactionCreateSerializer(serializers.ModelSerializer):
    id_account = serializers.IntegerField(write_only=True)
    id_category = serializers.UUIDField(write_only=True)
    id_payment_method = serializers.UUIDField(write_only=True)
    tags = serializers.ListField(
        child=serializers.UUIDField(),
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
        
    def validate_id_category(self, value):
        try:
            # Verificar se o UUID é válido e se a categoria existe
            category = Category.objects.get(id_category=value)
            return category  # Retorna a instância, não o UUID
        except Category.DoesNotExist:
            raise serializers.ValidationError("Categoria não encontrada")
        except Exception as e:
            raise serializers.ValidationError(f"ID da categoria inválido: {str(e)}")
        
    def validate_id_payment_method(self, value):
        try:
            # Verificar se o UUID é válido e se o método existe
            payment_method = PaymentMethod.objects.get(id_payment_method=value)
            return payment_method  # Retorna a instância, não o UUID
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Método de pagamento não encontrado")
        except Exception as e:
            raise serializers.ValidationError(f"ID do método de pagamento inválido: {str(e)}")
        
    def validate_id_account(self, value):
        try:
            # Buscar a instância da conta
            account = Account.objects.get(id=value)
            return account.id  # Mantém o ID para usar depois
        except Account.DoesNotExist:
            raise serializers.ValidationError("Conta não encontrada")
        except Exception as e:
            raise serializers.ValidationError(f"ID da conta inválido: {str(e)}")
        
    def validate_tags(self, value):
        valid_tags = []
        user = self.context['request'].user
        
        for tag_uuid in value:
            try:
                # Tenta encontrar a tag pelo UUID
                tag = Tag.objects.get(id_tag=tag_uuid, id_user=user)
                valid_tags.append(tag.id_tag)  # Mantém o UUID
            except Tag.DoesNotExist:
                raise serializers.ValidationError(f"Tag com ID {tag_uuid} não encontrada")
        
        return valid_tags
    
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