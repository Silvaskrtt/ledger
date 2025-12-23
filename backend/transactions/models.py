import uuid
from django.db.models import Q, CheckConstraint
from django.utils import timezone
from django.db import models
from accounts.models import Account
from categories.models import Category
from payments.models import PaymentMethod, InstallmentPlan
from users.models import User
from tags.models import Tag


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
    
    id_transaction = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='BRL')
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    id_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions')
    
    id_category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='transactions')
    
    id_payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.CASCADE,
        related_name='transactions')
    
    id_installment_plan = models.ForeignKey(
        InstallmentPlan,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )
    
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
            )
        ]
        
    def __str__(self):
        return f"Transaction {self.id_transaction}: {self.direction} of {self.amount} {self.currency} on {self.occurred_at}"

class TransactionAccount(models.Model):
    id_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='transaction_accounts')

    id_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transaction_accounts')
    
    role = models.CharField(max_length=50)
    
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
        unique_together = [('id_transaction', 'id_account', 'role')] 


class TransactionTag(models.Model):
    id_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='transaction_tags')

    id_tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='transaction_tags')
    
    # Unique constraint to prevent duplicate tag assignments to the same transaction
    class Meta:
        verbose_name = "Transaction Tag"
        verbose_name_plural = "Transaction Tags"
        unique_together = [('id_transaction', 'id_tag')]