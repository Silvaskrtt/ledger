# backend/accounts/models.py

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import ValidationError

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
        """
        Crédito disponível para cartões de crédito.
        
        PADRÃO: Saldo de cartão é NEGATIVO (representa dívida)
        Exemplo: Limite 5000, Saldo -1000 (dívida de 1000)
        Disponível = Limite - Dívida = 5000 - 1000 = 4000
        """
        if self.is_credit_card and self.credit_limit:
            # Balance é NEGATIVO (ex: -1000 = dívida de 1000)
            # Pegar valor absoluto para calcular crédito disponível
            current_debt = abs(self.balance)  # abs(-1000) = 1000
            available = self.credit_limit - current_debt
            return max(0, available)  # Nunca retorna negativo
        return None
    
    def save(self, *args, **kwargs):
        """
        Não sobrescreve balance automaticamente por transações.
        Balance deve ser calculado apenas através de recalculate_account_balance().
        
        PADRÃO DE SALDO:
        - Contas normais: Pode ser qualquer valor
        - Cartões de crédito: Deve ser NEGATIVO ou ZERO (representa dívida)
        """
        if not self.pk:
            # Apenas na criação
            self.balance = self.initial_balance
        
        # VALIDAÇÃO CRÍTICA: Cartões de crédito nunca podem ter saldo positivo
        if self.is_credit_card and self.balance > 0:
            logger_instance = __import__('logging').getLogger(__name__)
            logger_instance.warning(
                f"Cartão de crédito '{self.name}' tem saldo positivo ({self.balance}). "
                f"Ajustando para 0."
            )
            self.balance = 0
        
        # Validar consistência
        self.clean()
        super().save(*args, **kwargs)
    
    def get_calculated_balance(self):
        """Calcula saldo baseado em transações (fonte da verdade)."""
        from transactions.services.balance_service import recalculate_account_balance
        return recalculate_account_balance(self)
    
    def refresh_balance(self):
        """Atualiza balance com valor calculado das transações."""
        calculated = self.get_calculated_balance()
        if self.balance != calculated:
            self.balance = calculated
            self.save(update_fields=['balance'])
        return self.balance
    
    @property
    def is_consistent(self):
        """Verifica se saldo armazenado = saldo calculado."""
        calculated = self.get_calculated_balance()
        return abs(self.balance - calculated) < 0.01

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
    
def clean(self):
        """Validações do modelo."""
        super().clean()
        
        if self.is_credit_card:
            # Cartões não podem ter saldo positivo
            if self.balance > 0:
                raise ValidationError({
                    'balance': 'Cartões de crédito não podem ter saldo positivo.'
                })
            
            # Dias devem estar entre 1 e 31
            if self.closing_day and not (1 <= self.closing_day <= 31):
                raise ValidationError({
                    'closing_day': 'Dia de fechamento deve estar entre 1 e 31.'
                })
            
            if self.due_day and not (1 <= self.due_day <= 31):
                raise ValidationError({
                    'due_day': 'Dia de vencimento deve estar entre 1 e 31.'
                })
    
        def save(self, *args, **kwargs):
            """Garante consistência ao salvar."""
            # Na criação, balance = initial_balance
            if not self.pk:
                self.balance = self.initial_balance
              
            # Validar consistência   
            self.clean()
            super().save(*args, **kwargs)
        
        @property
        def is_credit_card(self):
            return self.type == 'CREDIT_CARD'
        
        @property
        def available_credit(self):
            """Crédito disponível para cartões."""
            if self.is_credit_card and self.credit_limit:
                # Para cartões, balance é negativo (dívida)
                # Crédito disponível = limite + balance (balance é negativo)
                return self.credit_limit + self.balance  # Ex: 5000 + (-1000) = 4000
            return None
        
        def get_transaction_balance(self):
            """Calcula saldo baseado em transações (fonte da verdade)."""
            from transactions.services.balance_service import recalculate_account_balance
            return recalculate_account_balance(self)