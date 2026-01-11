# backend/payments/models.py

import uuid
from django.utils import timezone
from django.db.models import Q, CheckConstraint
from django.db import models
from accounts.models import Account
from django.contrib.auth.models import User
from categories.models import Category

class PaymentMethod(models.Model):
    TYPE_CHOICES = [
        ('CREDIT', 'Cartão de Crédito'),
        ('DEBIT', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('CASH', 'Dinheiro'),
        ('BANK_TRANSFER', 'Transferência Bancária'),
        ('BOLETO', 'Boleto'),
        ('CRYPTO', 'Criptomoeda'),
        ('OTHER', 'Outro'),
    ]
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='PIX'
        )
    
    payment_method = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='id_payment_method')
    description = models.CharField(max_length=100, null=True, blank=True)
    requires_account = models.BooleanField(default=True)
    allows_installments = models.BooleanField(default=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='payment_methods',
        db_column='id_user_id')
    
    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'type', 'description'],
                name='unique_payment_method_per_user'
            )
        ]


class InstallmentPlan(models.Model):
    installment_plan = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='id_installment_plan')
    
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    # Constraints to ensure total_amount is positive and below a certain limit
    
    installments = models.IntegerField()   
    start_date = models.DateField(default=timezone.now)
    
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Taxa de juros mensal em % (0 para sem juros)"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='installment_plans',
        db_column='id_user_id')

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='installment_plans',
        db_column='id_account_id')

    id_category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='installment_plans')

    class Meta:
        verbose_name = "Installment Plan"
        verbose_name_plural = "Installment Plans"
        constraints = [
            CheckConstraint(condition=Q(total_amount__gt=0), name='total_amount_positive'),
            CheckConstraint(condition=Q(installments__gt=0), name='installments_positive'),
            CheckConstraint(condition=Q(installments__lte=360), name='installments_max_limit'),
            CheckConstraint(condition=Q(interest_rate__gte=0), name='interest_rate_non_negative'),
            CheckConstraint(condition=Q(interest_rate__lte=100), name='interest_rate_max_100'),
        ]
        
    def __str__(self):
        return f"Total: {self.total_amount}"