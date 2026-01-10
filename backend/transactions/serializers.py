# backend/transactions/serializers.py

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Transaction, TransactionAccount, TransactionTag
from django.utils import timezone
from recurrence.models import RecurrenceRule
from categories.models import Category
from payments.models import PaymentMethod
from accounts.models import Account
from tags.models import Tag
from .services.transaction_service import create_transaction_service

class TransactionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer unificado para criação de transações.
    Suporta: Manual, Parcelado, Recorrente
    """
    # Campos básicos (comuns a todos os tipos)
    id_category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.none(),
        write_only=True
    )
    id_payment_method = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.none(),
        write_only=True
    )
    id_account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.none(),
        write_only=True 
    )
    amount = serializers.DecimalField(
        max_digits=14, 
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    currency = serializers.ChoiceField(
        choices=['BRL', 'USD', 'EUR'],
        default='BRL'
    )
    direction = serializers.ChoiceField(
        choices=['IN', 'OUT']
    )
    origin = serializers.ChoiceField(
        choices=['MANUAL', 'INSTALLMENT', 'RECURRENT'],
        default='MANUAL'
    )
    occurred_at = serializers.DateTimeField(
        default=timezone.now
    )
    tags = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Descrição da transação"
    )
    
    # Campos específicos para parcelamento
    installments = serializers.IntegerField(
        min_value=2,
        max_value=360,
        required=False,
        write_only=True,
        help_text="Número de parcelas (apenas para origin='INSTALLMENT')"
    )
    interest_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0'),
        max_value=Decimal('100'),
        required=False,
        default=Decimal('0'),
        write_only=True,
        help_text="Taxa de juros mensal em % (0 para sem juros)"
    )
    
    # Campos específicos para recorrência
    recurrence_frequency = serializers.ChoiceField(
        choices=[
            ('DAILY', 'Diário'),
            ('WEEKLY', 'Semanal'),
            ('BIWEEKLY', 'Quinzenal'),
            ('MONTHLY', 'Mensal'),
            ('QUARTERLY', 'Trimestral'),
            ('SEMIANNUAL', 'Semestral'),
            ('ANNUAL', 'Anual'),
        ],
        required=False,
        write_only=True,
        help_text="Frequência (apenas para origin='RECURRENT')"
    )
    max_recurrences = serializers.IntegerField(
        min_value=1,
        required=False,
        write_only=True,
        help_text="Número máximo de ocorrências (opcional)"
    )
    
    class Meta:
        model = Transaction
        fields = [
            'id_category', 'id_payment_method', 'id_account', 'amount',
            'currency', 'direction', 'origin', 'occurred_at', 'tags',
            'installments', 'interest_rate', 'recurrence_frequency',
            'max_recurrences', 'description'
        ]

        read_only_fields = ['id_transaction', 'created_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context['request'].user
        
        # Filtrar querysets por usuário
        self.fields['id_category'].queryset = Category.objects.filter(id_user=user)
        self.fields['id_payment_method'].queryset = PaymentMethod.objects.filter(id_user=user)
        self.fields['id_account'].queryset = Account.objects.filter(user=user)
        self.fields['tags'].queryset = Tag.objects.filter(id_user=user)
        
        # Debug: log das tags disponíveis
        tags_count = self.fields['tags'].queryset.count()
        logger.debug(f"Usuário {user.username} tem {tags_count} tags disponíveis")

    def validate(self, data):
        """Validações cruzadas entre campos."""
        origin = data.get('origin', 'MANUAL')
        
        # OBTER O USUÁRIO PRIMEIRO
        user = self.context['request'].user
        
        # DEBUG: Log do que está chegando
        logger.debug(f"=== VALIDATE TRANSACTION ===")
        logger.debug(f"Usuário: {user.username}")
        logger.debug(f"Dados recebidos: {data}")
        
        tags = data.get('tags', [])
        logger.debug(f"Tags recebidas: {tags}")
        logger.debug(f"Número de tags: {len(tags)}")
        
        # Validação de tags (agora são UUIDs strings)
        for tag_id in tags:
            try:
                # Converter string UUID para objeto Tag
                from tags.models import Tag
                tag = Tag.objects.get(id_tag=tag_id, id_user=user)
                logger.debug(f"  Tag válida: {tag.id_tag} | Nome: {tag.name} | Usuário: {tag.id_user.username}")
            except Tag.DoesNotExist:
                raise serializers.ValidationError({
                    "tags": f"Tag com ID {tag_id} não encontrada ou não pertence ao usuário."
                })
        
        # Validar ownership de cada campo
        if 'id_category' in data and data['id_category'].id_user != user:
            raise serializers.ValidationError("Category não pertence ao usuário")
        
        # Validações para parcelamento
        if origin == 'INSTALLMENT':
            installments = data.get('installments')
            if not installments:
                raise serializers.ValidationError({
                    "installments": "Para transação parcelada, informe o número de parcelas."
                })
            if installments < 2:
                raise serializers.ValidationError({
                    "installments": "Parcelamento requer pelo menos 2 parcelas."
                })
                
            # Garantir que interest_rate tenha valor padrão 0
            if 'interest_rate' not in data:
                data['interest_rate'] = Decimal('0')
        
        # Validações para recorrência
        if origin == 'RECURRENT':
            if not data.get('recurrence_frequency'):
                raise serializers.ValidationError({
                    "recurrence_frequency": "Para transação recorrente, informe a frequência."
                })
        
        # Valida que campos específicos não são usados com origem errada
        if origin == 'MANUAL':
            if data.get('installments'):
                raise serializers.ValidationError({
                    "installments": "Campo 'installments' só é válido para origin='INSTALLMENT'."
                })
            if data.get('recurrence_frequency'):
                raise serializers.ValidationError({
                    "recurrence_frequency": "Campo 'recurrence_frequency' só é válido para origin='RECURRENT'."
                })
        
        # Valida data futura (pode ser permitida para agendamentos)
        occurred_at = data.get('occurred_at', timezone.now())
        if occurred_at > timezone.now() and origin == 'MANUAL':
            # Pode querer permitir agendamentos, ajuste conforme necessidade
            pass
        
        return data
    
    def create(self, validated_data):
        """Usa o serviço para criar a transação."""
        request = self.context['request']
        
        #Debug
        print(f"Usuário autenticado: {request.user}")
        print(f"Está autenticado? {request.user.is_authenticated}")
        
        # Extrai dados específicos
        tag_ids = validated_data.pop('tags', [])
        installments = validated_data.pop('installments', None)
        interest_rate = validated_data.pop('interest_rate', Decimal('0'))
        recurrence_frequency = validated_data.pop('recurrence_frequency', None)
        max_recurrences = validated_data.pop('max_recurrences', None)
        
        # Converter IDs de tag para objetos Tag
        tag_objects = []
        for tag_id in tag_ids:
            try:
                tag = Tag.objects.get(id_tag=tag_id, id_user=request.user)
                tag_objects.append(tag)
            except Tag.DoesNotExist:
                logger.warning(f"Tag {tag_id} não encontrada para usuário {request.user}")
        
        # Chama o serviço unificado
        result = create_transaction_service(
            user=request.user,
            tags=tag_objects,
            installments=installments,
            interest_rate=interest_rate,
            recurrence_frequency=recurrence_frequency,
            max_recurrences=max_recurrences,
            **validated_data
        )
        
        return result

# Manter os outros serializers existentes
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

class RecurrenceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrenceRule
        fields = '__all__'