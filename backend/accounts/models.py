# backend/accounts/models.py

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

class Account(models.Model):
    TYPE_CHOICES = [
        ('CHECKING', 'Conta Corrente'),
        ('SAVINGS', 'Conta Poupança'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('INVESTMENT', 'Investimentos'),
        ('CASH', 'Dinheiro'),
        ('OTHER', 'Outro'),
    ]
    
    id_account = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='CHECKING'
    )
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    credit_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        default=0
    )
    closing_day = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    due_day = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def is_credit_card(self):
        return self.type == 'CREDIT_CARD'

class CreditCardBill(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Aberta'),
        ('CLOSED', 'Fechada'),
        ('PAID', 'Paga'),
        ('OVERDUE', 'Vencida'),
    ]
    
    id_bill = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    credit_card = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='bills',
        limit_choices_to={'type': 'CREDIT_CARD'}
    )
    
    # Período da fatura
    start_date = models.DateField()  # Início do ciclo
    end_date = models.DateField()    # Fim do ciclo (dia do fechamento)
    due_date = models.DateField()    # Data de vencimento
    
    # Valores
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    
    class Meta:
        unique_together = ['credit_card', 'start_date', 'end_date']
        ordering = ['-end_date']
    
    def __str__(self):
        return f"Fatura {self.end_date.strftime('%m/%Y')} - {self.credit_card.name}"