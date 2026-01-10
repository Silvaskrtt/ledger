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
    
    id_account = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Nome da Conta")
    
    # Saldo inicial e atual
    initial_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Saldo Inicial"
    )
    
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Saldo Atual"
    )
    
    # Informações da conta
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='CHECKING',
        verbose_name="Tipo de Conta"
    )
    
    bank_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name="Instituição Bancária"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição/Observações"
    )
    
    # Para cartões de crédito
    credit_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        default=0,
        verbose_name="Limite de Crédito"
    )
    
    closing_day = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Dia do Fechamento"
    )
    
    due_day = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Dia do Vencimento"
    )
    
    # Para personalização visual
    icon = models.CharField(
        max_length=50,
        default='wallet',
        blank=True,
        help_text="Ícone da conta (ex: wallet, credit-card, piggy-bank)"
    )
    
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Cor em hexadecimal (#RRGGBB)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Conta"
        verbose_name_plural = "Contas"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_account_name_per_user'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    @property
    def is_credit_card(self):
        return self.type == 'CREDIT_CARD'
    
    @property
    def available_credit(self):
        """Crédito disponível para cartões"""
        if self.is_credit_card and self.credit_limit:
            return self.credit_limit + self.balance  # balance é negativo para cartões
        return None
    
    def save(self, *args, **kwargs):
        # Na criação, define saldo atual igual ao inicial
        if not self.pk:
            self.balance = self.initial_balance
        super().save(*args, **kwargs)

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