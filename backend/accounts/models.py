# backend/accounts/models.py

from decimal import Decimal
from django.db.models import Sum
import uuid
import logging
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)

class Account(models.Model):
    TYPE_CHOICES = [
        ('CHECKING', 'Conta Corrente'),
        ('SAVINGS', 'Conta Poupança'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('INVESTMENT', 'Investimentos'),
        ('CASH', 'Dinheiro'),
        ('OTHER', 'Outro'),
    ]
    
    account = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        db_column='id_account'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True
    )
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
        
        REGRA CORRIGIDA:
        - Balance é NEGATIVO (ex: -1000 = dívida de 1000)
        - Available = Limite - (Valor Absoluto do Balance)
        - Ex: Limite 5000, Balance -1000 → Available = 5000 - 1000 = 4000
        """
        if self.is_credit_card and self.credit_limit:
            # Balance é NEGATIVO, pegar valor absoluto
            current_debt = abs(self.balance) if self.balance < 0 else 0
            available = self.credit_limit - current_debt
            return max(0, available)  # Nunca negativo
        return None
    
    def clean(self):
        """Validações do modelo."""
        super().clean()
        
        if self.is_credit_card:
            # Cartões NUNCA podem ter saldo positivo
            if self.balance > 0:
                self.balance = 0  # Corrige automaticamente
            
            # Validar dias
            if self.closing_day and not (1 <= self.closing_day <= 31):
                raise ValidationError({
                    'closing_day': 'Dia de fechamento deve estar entre 1 e 31.'
                })
            
            if self.due_day and not (1 <= self.due_day <= 31):
                raise ValidationError({
                    'due_day': 'Dia de vencimento deve estar entre 1 e 31.'
                })
    
    def save(self, *args, **kwargs):
        """
        Garante consistência ao salvar.
        
        PADRÃO DE SALDO:
        - Contas normais: Pode ser qualquer valor
        - Cartões de crédito: Deve ser NEGATIVO ou ZERO (representa dívida)
        """
        if not self.pk:
            # Apenas na criação
            self.balance = self.initial_balance
        
        # VALIDAÇÃO CRÍTICA: Cartões de crédito nunca podem ter saldo positivo
        if self.is_credit_card and self.balance > 0:
            logger.warning(
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
        constraints = [
            models.CheckConstraint(
                condition=models.Q(paid_amount__lte=models.F('total_amount')),
                name='paid_amount_lte_total'
            ),
            models.CheckConstraint(
                condition=models.Q(minimum_payment__lte=models.F('total_amount')),
                name='minimum_payment_lte_total'
            ),
            models.CheckConstraint(
                condition=models.Q(paid_amount__gte=0),
                name='paid_amount_non_negative'
            ),
            models.CheckConstraint(
                condition=models.Q(minimum_payment__gte=0),
                name='minimum_payment_non_negative'
            ),
        ]
        
    def recalculate_totals(self):
        """
        Recalcula totais da fatura baseado nas transações ativas.
        """
        # Compras vinculadas a esta fatura (não deletadas)
        purchases = self.bill_transactions.filter(
            transaction_type='PURCHASE',
            is_deleted=False
        )
        
        purchases_total = purchases.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Pagamentos vinculados a esta fatura (não deletados)
        payments = self.bill_transactions.filter(
            transaction_type='CREDIT_CARD_PAYMENT',
            is_deleted=False
        )
    
        payments_total = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Atualizar valores
        self.total_amount = purchases_total
        self.paid_amount = payments_total
        
        # Recalcular pagamento mínimo
        if self.total_amount > 0:
            self.minimum_payment = max(
                Decimal('0.01'),
                (self.total_amount * Decimal('0.10')).quantize(Decimal('0.01'))
            )
            self.minimum_payment = min(self.minimum_payment, self.total_amount)
        else:
            self.minimum_payment = Decimal('0.00')
        
        # Atualizar status
        if self.paid_amount >= self.total_amount:
            self.status = 'PAID'
        elif timezone.now().date() > self.due_date:
            self.status = 'OVERDUE'
        elif self.total_amount > 0:
            self.status = 'OPEN'
        else:
            self.status = 'CLOSED'
        
        self.save(update_fields=[
            'total_amount', 
            'paid_amount', 
            'minimum_payment', 
            'status'
        ])
        
        return {
            'total_amount': self.total_amount,
            'paid_amount': self.paid_amount,
            'pending': self.total_amount - self.paid_amount,
            'status': self.status
        }
        
    def clean(self):
        """Validações do modelo."""
        super().clean()
        
        # Verificar se paid_amount não excede total_amount
        if self.paid_amount > self.total_amount:
            raise ValidationError({
                'paid_amount': f'O valor pago (R${self.paid_amount}) '
                             f'não pode ser maior que o total da fatura (R${self.total_amount}).'
            })
    
    def save(self, *args, **kwargs):
        """Garante consistência ao salvar."""
        self.clean()
        super().save(*args, **kwargs)
        
    @property
    def transactions(self):
        """
        Propriedade para compatibilidade.
        Retorna bill_transactions (que é o nome correto do related_name).
        """
        return self.bill_transactions.all()
        
    def __str__(self):
        return f"Fatura {self.end_date.strftime('%m/%Y')} - {self.credit_card.name}"
    
class CreditCardPayment(models.Model):
    """
    Registro de pagamento de fatura de cartão de crédito.
    """
    id_payment = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    bill = models.ForeignKey(
        CreditCardBill,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    payment_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='credit_card_payments',
        help_text="Conta de onde saiu o dinheiro para pagar a fatura"
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(default=timezone.now)
    
    # Para registrar qual transação foi criada para este pagamento
    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_card_payment'
    )
    
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-paid_at']
        verbose_name = "Pagamento de Fatura"
        verbose_name_plural = "Pagamentos de Faturas"
        
    @property
    def transactions(self):
        """Propriedade para compatibilidade com código antigo"""
        return self.bill_transactions.all()
    
    def recalculate_totals(self):
        """
        Recalcula totais da fatura baseado nas transações ativas.
        """
        # Usar 'bill_transactions' em vez de 'transactions'
        purchases = self.bill_transactions.filter(
            transaction_type='PURCHASE',
            is_deleted=False
        )
        
        purchases_total = purchases.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Pagamentos vinculados a esta fatura (não deletados)
        payments = self.bill_transactions.filter(
            transaction_type='CREDIT_CARD_PAYMENT',
            is_deleted=False
        )
    
    def __str__(self):
        return f"Pagamento de R${self.amount} para fatura {self.bill}"