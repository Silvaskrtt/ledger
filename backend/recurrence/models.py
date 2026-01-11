# backend/recurrence/models.py

import uuid
from django.db import models
from categories.models import Category
from django.contrib.auth.models import User
from payments.models import PaymentMethod
from accounts.models import Account
from django.db.models import Q, CheckConstraint


class RecurrenceRule(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Diário'),
        ('WEEKLY', 'Semanal'),
        ('BIWEEKLY', 'Quinzenal'),
        ('MONTHLY', 'Mensal'),
        ('QUARTERLY', 'Trimestral'),
        ('SEMIANNUAL', 'Semestral'),
        ('ANNUAL', 'Anual'),
    ]

    DIRECTION_CHOICES = [
        ('IN', 'Income'),
        ('OUT', 'Expense'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Ativa'),
        ('PAUSED', 'Pausada'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
    ]

    recurrence_rule = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='id_recurrence_rule'
    )
    
    frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES)
    next_execution = models.DateField()
    max_executions = models.IntegerField(null=True, blank=True)
    executions_count = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    direction = models.CharField(max_length=50, choices=DIRECTION_CHOICES)
    
    # NOVOS CAMPOS
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="Status da regra de recorrência"
    )
    last_execution = models.DateField(
        null=True,
        blank=True,
        help_text="Data da última execução"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Recurrence Rule"
        verbose_name_plural = "Recurrence Rules"
        constraints = [
            CheckConstraint(
                condition=Q(max_executions__gt=0) | Q(max_executions__isnull=True),
                name='max_executions_positive_or_null'
            ),
            CheckConstraint(
                condition=Q(executions_count__gte=0),
                name='executions_count_non_negative'
            )
        ]
    
    
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        db_column='id_user',
        related_name='recurrence_rules')

    category = models.ForeignKey(
        to=Category,
        on_delete=models.CASCADE,
        related_name='recurrence_rules',
        db_column='id_category')

    payment_method = models.ForeignKey(
        to=PaymentMethod,
        on_delete=models.CASCADE,
        related_name='recurrence_rules',
        db_column='id_payment_method')

    account = models.ForeignKey(
        to=Account,
        on_delete=models.CASCADE,
        related_name='recurrence_rules',
        db_column='id_account')

    def __str__(self):
        return f"{self.get_frequency_display()} - R${self.amount} ({self.get_direction_display()}) - {self.get_status_display()}"
    
    def is_active(self):
        """Verifica se a regra está ativa e pode ser executada."""
        if self.status != 'ACTIVE':
            return False
        
        # Verificar se atingiu max_executions
        if self.max_executions and self.executions_count >= self.max_executions:
            return False
        
        return True