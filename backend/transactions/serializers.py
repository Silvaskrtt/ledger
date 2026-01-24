import logging
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from .models import Transaction, TransactionAccount, TransactionTag
from recurrence.models import RecurrenceRule
from categories.models import Category
from payments.models import PaymentMethod
from accounts.models import Account
from tags.models import Tag
from .services.transaction_service import create_transaction_service, validate_payment_method_compatibility
from transactions.services.balance_service import recalculate_account_balance

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        
        # Debug: log das tags disponíveis
        tags_count = Tag.objects.filter(user=user).count()
        logger.debug(f"Usuário {user.username} tem {tags_count} tags disponíveis")

    def validate(self, data):
        """Validações cruzadas entre campos."""
        logger.info("=== VALIDATE START ===")
        
        user = self.context['request'].user
        origin = data.get('origin', 'MANUAL')
        direction = data.get('direction')
        amount = data.get('amount')
        account = data.get('account')
        payment_method = data.get('payment_method')
        category = data.get('category')
        tags = data.get('tags', [])
        
        # LOG DETALHADO PARA DEBUG
        logger.info(f"User: {user.username}")
        logger.info(f"Origin: {origin}")
        logger.info(f"Direction: {direction}")
        logger.info(f"Amount: {amount}")
        logger.info(f"Account: {account}")
        logger.info(f"Payment method: {payment_method}")
        logger.info(f"Category: {category}")
        logger.info(f"Tags: {tags}")
        
        # ============================================
        # VALIDAÇÕES BÁSICAS
        # ============================================
        if not account:
            raise serializers.ValidationError({"account": "Conta é obrigatória"})
        
        if not payment_method:
            raise serializers.ValidationError({"payment_method": "Método de pagamento é obrigatório"})
        
        if not category:
            raise serializers.ValidationError({"category": "Categoria é obrigatória"})
        
        if not amount or amount <= 0:
            raise serializers.ValidationError({"amount": "Valor deve ser maior que zero"})
        
        # ============================================
        # OBTER OBJETOS
        # ============================================
        try:
            # Converter IDs para objetos
            if isinstance(account, Account):
                account_obj = account
            else:
                account_obj = Account.objects.get(pk=account, user=user)
            logger.info(f"Account encontrada: {account_obj.name} ({account_obj.type})")
            
            if isinstance(payment_method, PaymentMethod):
                payment_method_obj = payment_method
            else:
                payment_method_obj = PaymentMethod.objects.get(pk=payment_method, user=user)
            logger.info(f"Payment method encontrado: {payment_method_obj.description} ({payment_method_obj.type})")
            
            if isinstance(category, Category):
                category_obj = category
            else:
                category_obj = Category.objects.get(pk=category, user=user)
            logger.info(f"Category encontrada: {category_obj.name}")
            
        except Account.DoesNotExist:
            raise serializers.ValidationError({"account": "Conta não encontrada"})
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError({"payment_method": "Método de pagamento não encontrado"})
        except Category.DoesNotExist:
            raise serializers.ValidationError({"category": "Categoria não encontrada"})
        
        # ============================================
        # VALIDAR COMPATIBILIDADE
        # ============================================
        is_compatible = validate_payment_method_compatibility(
            payment_method_obj.type,
            account_obj.type
        )
        logger.info(f"Compatibilidade: {is_compatible}")
        
        if not is_compatible:
            error_msg = (
                f"Método de pagamento '{payment_method_obj.get_type_display()}' "
                f"não é compatível com conta '{account_obj.name}' ({account_obj.get_type_display()})."
            )
            raise serializers.ValidationError({
                "payment_method": error_msg
            })
        
        # ============================================
        # VALIDAR SALDO/LIMITE
        # ============================================
        if direction == 'OUT':
            if account_obj.is_credit_card:
                # Para cartões de crédito, verificar limite
                available_credit = account_obj.available_credit
                if amount > available_credit:
                    raise serializers.ValidationError({
                        "amount": f"Limite de crédito insuficiente no cartão {account_obj.name}. "
                                f"Crédito disponível: R${available_credit:.2f}"
                    })
            else:
                # Para contas normais, verificar saldo
                if amount > account_obj.balance:
                    raise serializers.ValidationError({
                        "amount": f"Saldo insuficiente na conta {account_obj.name}. "
                                f"Saldo atual: R${account_obj.balance:.2f}"
                    })
        
        # ============================================
        # VALIDAR TAGS
        # ============================================
        tag_objects = []
        for tag_id in tags:
            try:
                tag = Tag.objects.get(tag=tag_id, user=user)
                tag_objects.append(tag)
                logger.info(f"Tag válida: {tag.name}")
            except Tag.DoesNotExist:
                raise serializers.ValidationError({
                    "tags": f"Tag com ID {tag_id} não encontrada ou não pertence ao usuário."
                })
        
        # ============================================
        # VALIDAÇÕES ESPECÍFICAS POR ORIGEM
        # ============================================
        if origin == 'INSTALLMENT':
            installments = data.get('installments')
            if not installments or installments < 2:
                raise serializers.ValidationError({
                    "installments": "Para transação parcelada, informe o número de parcelas (mínimo 2)."
                })
                
            if 'interest_rate' not in data:
                data['interest_rate'] = Decimal('0')
        
        elif origin == 'RECURRENT':
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
        
        # Valida data futura
        occurred_at = data.get('occurred_at', timezone.now())
        if occurred_at > timezone.now() and origin == 'MANUAL':
            logger.info(f"Transação agendada para o futuro: {occurred_at}")
        
        logger.info("=== VALIDATE END ===")
        
        # Adicionar objetos ao validated_data para uso no create
        data['account_obj'] = account_obj
        data['payment_method_obj'] = payment_method_obj
        data['category_obj'] = category_obj
        data['tag_objects'] = tag_objects
        
        return data
    
    def create(self, validated_data):
        """Cria uma nova transação usando o serviço."""
        logger.info("=== CREATE TRANSACTION ===")
        
        # Extrair objetos do validated_data
        account_obj = validated_data.pop('account_obj', None)
        payment_method_obj = validated_data.pop('payment_method_obj', None)
        category_obj = validated_data.pop('category_obj', None)
        tag_objects = validated_data.pop('tag_objects', [])
        
        if not all([account_obj, payment_method_obj, category_obj]):
            raise ValueError("Objetos necessários não encontrados no validated_data")
        
        # Chamar serviço de criação
        result = create_transaction_service(
            user=self.context['request'].user,
            amount=validated_data['amount'],
            direction=validated_data['direction'],
            category=category_obj,
            payment_method=payment_method_obj,
            account=account_obj,
            origin=validated_data['origin'],
            tags=tag_objects,
            currency=validated_data.get('currency', 'BRL'),
            occurred_at=validated_data.get('occurred_at'),
            installments=validated_data.get('installments'),
            interest_rate=validated_data.get('interest_rate', Decimal('0')),
            recurrence_frequency=validated_data.get('recurrence_frequency'),
            max_recurrences=validated_data.get('max_recurrences'),
            description=validated_data.get('description', '')
        )
        
        return result


class TransactionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de transações.
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

    def update(self, instance, validated_data):
        """
        Atualiza uma transação existente.
        """
        logger.info(f"=== UPDATE TRANSACTION {instance.transaction} ===")
        
        # 1. CAPTURAR INFORMAÇÕES ANTIGAS
        old_accounts = list(instance.transaction_accounts.all())
        old_amount = instance.amount
        old_direction = instance.direction
        
        # 2. PROCESSAR TAGS
        tag_ids = validated_data.pop('tags', [])
        tag_objects = []
        user = self.context['request'].user
        
        for tag_id in tag_ids:
            try:
                tag = Tag.objects.get(tag=tag_id, user=user)
                tag_objects.append(tag)
            except Tag.DoesNotExist:
                logger.warning(f"Tag não encontrada: {tag_id}")
        
        # 3. IDENTIFICAR MUDANÇA DE CONTA
        new_account = validated_data.get('account')
        is_account_changed = new_account and (
            not old_accounts or 
            old_accounts[0].account != new_account
        )
        
        # 4. ATUALIZAR CAMPOS BÁSICOS
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # 5. SE CONTA MUDOU, ATUALIZAR RELACIONAMENTOS
        if is_account_changed:
            # Remover todas as relações antigas
            instance.transaction_accounts.all().delete()
            
            # Criar nova relação
            role = 'source' if instance.direction == 'OUT' else 'destination'
            TransactionAccount.objects.create(
                transaction=instance,
                account=new_account,
                role=role
            )
            
            logger.info(f"Conta da transação atualizada: {old_accounts[0].account.name if old_accounts else 'Nenhuma'} → {new_account.name}")
        
        # 6. ATUALIZAR TAGS
        instance.tags.clear()
        for tag in tag_objects:
            TransactionTag.objects.create(
                transaction=instance,
                tag=tag
            )
        
        # 7. RECALCULAR SALDOS DE TODAS AS CONTAS AFETADAS
        # Contas antigas
        for ta in old_accounts:
            recalculate_account_balance(ta.account)
        
        # Nova conta
        if is_account_changed:
            recalculate_account_balance(new_account)
        else:
            # Se não mudou conta, recalcular apenas a conta atual
            current_account = instance.transaction_accounts.first().account
            recalculate_account_balance(current_account)
        
        # 8. ATUALIZAR FATURAS SE FOR CARTÃO DE CRÉDITO
        if instance.credit_card_bill:
            instance.credit_card_bill.recalculate_totals()
        
        # Para cartões de crédito antigos (se mudou de conta)
        for ta in old_accounts:
            if ta.account.type == 'CREDIT_CARD' and ta.account != new_account:
                # Recalcular faturas do cartão antigo
                from accounts.models import CreditCardBill
                bills = CreditCardBill.objects.filter(credit_card=ta.account)
                for bill in bills:
                    bill.recalculate_totals()
        
        logger.info(f"Transação {instance.transaction} atualizada com sucesso")
        
        return instance


class TransactionAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionAccount
        fields = ['transaction', 'account', 'role']
    
    def validate(self, data):
        """Validações cruzadas entre campos."""
        transaction = data.get('transaction')
        account = data.get('account')
        
        # Validar ownership
        if transaction and account:
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
            if tag.user != transaction.user:
                raise serializers.ValidationError(
                    "A tag não pertence ao mesmo usuário da transação."
                )
        
        return data


class RecurrenceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrenceRule
        fields = '__all__'