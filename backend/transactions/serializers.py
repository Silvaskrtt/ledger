# backend/transactions/serializers.py

import logging

from transactions.services.balance_service import recalculate_account_balance
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
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.none(),
        write_only=True
    )
    payment_method = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.none(),
        write_only=True
    )
    account = serializers.PrimaryKeyRelatedField(
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
            'category', 'payment_method', 'account', 'amount',
            'currency', 'direction', 'origin', 'occurred_at', 'tags',
            'installments', 'interest_rate', 'recurrence_frequency',
            'max_recurrences', 'description'
        ]

        read_only_fields = ['transaction', 'created_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context['request'].user
        
        # Filtrar querysets por usuário
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=user)
        self.fields['account'].queryset = Account.objects.filter(user=user)
        self.fields['tags'].queryset = Tag.objects.filter(user=user)
        
        # Debug: log das tags disponíveis
        tags_count = self.fields['tags'].queryset.count()
        logger.debug(f"Usuário {user.username} tem {tags_count} tags disponíveis")

    def validate(self, data):
        """Validações cruzadas entre campos."""
        origin = data.get('origin', 'MANUAL')
        direction = data.get('direction')
        amount = data.get('amount')
        account = data.get('account')
        payment_method = data.get('payment_method')
        
        # OBTER O USUÁRIO PRIMEIRO
        user = self.context['request'].user
        
        # DEBUG: Log do que está chegando
        logger.debug(f"=== VALIDATE TRANSACTION ===")
        logger.debug(f"Usuário: {user.username}")
        logger.debug(f"Dados recebidos: {data}")
        
        tags = data.get('tags', [])
        logger.debug(f"Tags recebidas: {tags}")
        logger.debug(f"Número de tags: {len(tags)}")
        
        # Validar saldo da conta
        if account and direction and amount:
            try:
                account_obj = Account.objects.get(pk=account.account if hasattr(account, 'account') else account, user=user)
                
                # VALIDAÇÃO ESPECÍFICA PARA CARTÕES DE CRÉDITO
                if account_obj.is_credit_card:
                    available_credit = account_obj.available_credit
                    
                    if direction == 'OUT':
                        # Para compras no cartão, verificar limite
                        if amount > available_credit:
                            raise serializers.ValidationError({
                                "amount": f"Limite de crédito insuficiente no cartão {account_obj.name}. "
                                         f"Crédito disponível: R${available_credit:.2f}"
                            })
                        
                        # Verificar se método de pagamento é CREDIT para compras no cartão
                        if payment_method and payment_method.type != 'CREDIT':
                            raise serializers.ValidationError({
                                "payment_method": "Para compras no cartão de crédito, "
                                                "o método de pagamento deve ser 'Crédito'"
                            })
                    
                    elif direction == 'IN':
                        # Para pagamentos de fatura, verificar se método é adequado
                        if payment_method and payment_method.type in ['CREDIT', 'DEBIT']:
                            raise serializers.ValidationError({
                                "payment_method": "Para pagamento de fatura de cartão, "
                                                "use métodos como PIX, Transferência ou Dinheiro"
                            })
                
                else:
                    # Conta normal: verificar saldo para saídas
                    if direction == 'OUT' and account_obj.balance < amount:
                        raise serializers.ValidationError({
                            "amount": f"Saldo insuficiente na conta {account_obj.name}. "
                                     f"Saldo atual: R${account_obj.balance:.2f}"
                        })
                        
            except Account.DoesNotExist:
                raise serializers.ValidationError({"account": "Conta não encontrada"})
        
        # Validação de tags (agora são UUIDs strings)
        for tag_id in tags:
            try:
                # Converter string UUID para objeto Tag
                from tags.models import Tag
                tag = Tag.objects.get(tag=tag_id, user=user)
                logger.debug(f"  Tag válida: {tag.tag} | Nome: {tag.name} | Usuário: {tag.user.username}")
            except Tag.DoesNotExist:
                raise serializers.ValidationError({
                    "tags": f"Tag com ID {tag_id} não encontrada ou não pertence ao usuário."
                })
        
        # Validar ownership de cada campo
        if 'category' in data and data['category'].user != user:
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
        
        if account and payment_method:
            from .services.transaction_service import validate_payment_method_compatibility
            
            if not validate_payment_method_compatibility(payment_method.type, account.type):
                raise serializers.ValidationError({
                    "payment_method": f"Método de pagamento '{payment_method.get_type_display()}' "
                                        f"não é compatível com conta '{account.name}' ({account.get_type_display()})."
                })
        
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
                tag = Tag.objects.get(tag=tag_id, user=request.user)
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
    
    def update(self, instance, validated_data):
        """
        Atualiza uma transação existente.
        """
        # Remover transação antiga do saldo
        old_amount = instance.amount
        old_direction = instance.direction
        
        # Processar tags
        tag_ids = validated_data.pop('tags', [])
        tag_objects = []
        for tag_id in tag_ids:
            try:
                tag = Tag.objects.get(tag=tag_id, user=self.context['request'].user)
                tag_objects.append(tag)
            except Tag.DoesNotExist:
                pass
        
        # Atualizar campos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Atualizar tags
        instance.tags.clear()
        for tag in tag_objects:
            TransactionTag.objects.create(transaction=instance, tag=tag)
        
        # Recalcular saldo das contas
        for ta in instance.transaction_accounts.all():
            recalculate_account_balance(ta.account)
        
        return instance

# Manter os outros serializers existentes
class TransactionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de transações.
    Não precisa de todos os campos do TransactionCreateSerializer.
    """
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.none(),
        required=False
    )
    payment_method = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.none(),
        required=False
    )
    account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.none(),
        required=False
    )
    amount = serializers.DecimalField(
        max_digits=14, 
        decimal_places=2,
        min_value=Decimal('0.01'),
        required=False
    )
    currency = serializers.ChoiceField(
        choices=['BRL', 'USD', 'EUR'],
        required=False
    )
    direction = serializers.ChoiceField(
        choices=['IN', 'OUT'],
        required=False
    )
    origin = serializers.ChoiceField(
        choices=['MANUAL', 'INSTALLMENT', 'RECURRENT'],
        required=False
    )
    occurred_at = serializers.DateTimeField(
        required=False
    )
    tags = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )
    
    class Meta:
        model = Transaction
        fields = [
            'category', 'payment_method', 'account', 'amount',
            'currency', 'direction', 'origin', 'occurred_at', 'tags',
            'description'
        ]
        read_only_fields = ['transaction', 'created_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context['request'].user
        
        # Filtrar querysets por usuário
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=user)
        self.fields['account'].queryset = Account.objects.filter(user=user)

class TransactionAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionAccount
        fields = ['transaction', 'account', 'role']
    
    def validate(self, data):
        """Validar que account pertence ao mesmo user que a transaction."""
        transaction = data.get('transaction')
        account = data.get('account')
        
        if transaction and account:
            # Validar propriedade
            if account.user != transaction.user:
                raise serializers.ValidationError(
                    "A conta não pertence ao mesmo usuário da transação."
                )
        
        return data

class TransactionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionTag
        fields = ['transaction', 'tag']
    
    def validate(self, data):
        """Validar que tag pertence ao mesmo user que a transaction."""
        transaction = data.get('transaction')
        tag = data.get('tag')
        
        if transaction and tag:
            # Validar propriedade
            if tag.user != transaction.user:
                raise serializers.ValidationError(
                    "A tag não pertence ao mesmo usuário da transação."
                )
        
        return data

class RecurrenceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrenceRule
        fields = '__all__'