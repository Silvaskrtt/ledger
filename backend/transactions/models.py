# backend/transactions/models.py

import uuid
from django.db.models import Q, F, CheckConstraint, Manager
from django.utils import timezone
from django.db import models
from accounts.models import Account
from categories.models import Category
from payments.models import PaymentMethod, InstallmentPlan
from django.contrib.auth.models import User
from tags.models import Tag


class NotDeletedManager(Manager):
    """Manager que filtra apenas transações não deletadas"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllTransactionsManager(Manager):
    """Manager que retorna TODAS as transações, incluindo deletadas"""
    def get_queryset(self):
        return super().get_queryset()


class Transaction(models.Model):
    DIRECTION_CHOICES = [
        ('IN', 'Income'),
        ('OUT', 'Expense'),
    ]
    
    ORIGIN_CHOICES = [
        ('MANUAL', 'Manual'),
        ('RECURRENT', 'Recurrent'),
        ('INSTALLMENT', 'Installment'),
    ]
    
    CURRENCY_CHOICES = [
    ('BRL', 'Brazilian Real'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ]
    
    transaction = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='id_transaction'
    )
    
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    
    occurred_at = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='BRL')
    
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    
    description = models.CharField(max_length=255, blank=True, null=True, help_text="Descrição da transação")
    
    installment_number = models.IntegerField(null=True, blank=True, help_text="Número da parcela (apenas para parcelamentos)")
    
    total_installments = models.IntegerField(null=True, blank=True, help_text="Total de parcelas (apenas para parcelamentos)")
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        db_column='id_user_id')
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='transactions',
        db_column='id_category_id')
    
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.CASCADE,
        related_name='transactions',
        db_column='id_payment_method_id')
    
    installment_plan = models.ForeignKey(
        InstallmentPlan,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True,
        db_column='id_installment_plan_id'
    )
    
    credit_card_bill = models.ForeignKey(
        'accounts.CreditCardBill',  # String reference
        on_delete=models.SET_NULL,
        related_name='transactions',
        null=True,
        blank=True,
        help_text="Fatura do cartão de crédito onde esta transação será incluída"
    )
    
    # Relacionamento muitos-para-muitos com tags
    tags = models.ManyToManyField(
        Tag,
        through='TransactionTag',
        related_name='transactions'
    )
    
    # Gerenciador customizado para filtrar transações não deletadas
    objects = NotDeletedManager()  # Default: apenas ativas
    all_objects = AllTransactionsManager()  # Acesso a todas, incluindo deletadas
    
    # Constraints to ensure direction is either 'income' or 'expense' and amount is positive
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        constraints = [
            CheckConstraint(
                condition=Q(direction__in=['IN', 'OUT']),
                name='valid_transaction_direction'
            ),
            CheckConstraint(
                condition=Q(amount__gt=0),
                name='amount_positive'
            ),
            CheckConstraint(
                condition=(
                    Q(installment_number__isnull=True) | 
                    Q(installment_number__gt=0)
                ),
                name='valid_installment_number'
            ),
            CheckConstraint(
                condition=(
                    Q(total_installments__isnull=True) | 
                    Q(total_installments__gt=0)
                ),
                name='valid_total_installments'
            ),
            CheckConstraint(
                condition=(
                    Q(installment_number__isnull=True) |
                    Q(total_installments__isnull=True) |
                    Q(installment_number__lte=F('total_installments'))
                ),
                name='installment_number_lte_total'
            )
        ]
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Transaction {self.transaction}: {self.direction} of {self.amount} {self.currency} on {self.occurred_at}"

class TransactionAccount(models.Model):
    ROLE_CHOICES = [
        ('source', 'Source Account'),
        ('destination', 'Destination Account'),
    ]
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='transaction_accounts',
        db_column='id_transaction_id')

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transaction_accounts',
        db_column='id_account_id')
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='source'
    )
    
    class Meta:
        verbose_name = "Transaction Account"
        verbose_name_plural = "Transaction Accounts"
        constraints = [
            CheckConstraint(
                condition=Q(role__in=['source', 'destination']),
                name='valid_account_role'
            )
        ]
        
        # Unique constraint to prevent duplicate account-role assignments for the same transaction
        unique_together = [('transaction', 'account', 'role')] 


class TransactionTag(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='transaction_tags',
        db_column='id_transaction_id')

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='transaction_tags',
        db_column='id_tag_id')
    
    # Unique constraint to prevent duplicate tag assignments to the same transaction
    class Meta:
        verbose_name = "Transaction Tag"
        verbose_name_plural = "Transaction Tags"
        unique_together = [('transaction', 'tag')]

