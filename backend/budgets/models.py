# backend/budgets/models.py

import uuid
from datetime import timedelta
from django.db import models
from django.db.models import CheckConstraint, Q
from django.contrib.auth.models import User
from django.utils.timezone import now
from categories.models import Category


class Budget(models.Model):
    PERIOD_TYPE_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Ativo'),
        ('COMPLETED', 'Cumprido'),
        ('EXCEEDED', 'Excedido'),
        ('EXPIRED', 'Expirado'),
    ]

    budget = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='id_budget'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budgets',
        db_column='id_user_id',
        db_index=True)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField(null=True, blank=True)  # NOVO: data de fim
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE'
    )  # NOVO: status do orçamento
    created_at = models.DateTimeField(auto_now_add=True)  # NOVO: rastreamento
    updated_at = models.DateTimeField(auto_now=True)  # NOVO: rastreamento
    deleted_at = models.DateTimeField(null=True, blank=True)  # Soft delete
    is_deleted = models.BooleanField(default=False)  # Soft delete

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'period_type', 'period_start'],
                name='unique_budget_period'
            ),
            models.CheckConstraint(
                condition=models.Q(period_end__gte=models.F('period_start')),
                name='period_end_gte_start'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['period_start', 'period_end']),
        ]

    def __str__(self):
        return f"Budget {self.period_type} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        """Calcular period_end automaticamente se não informado."""
        if not self.period_end:
            if self.period_type == 'DAILY':
                self.period_end = self.period_start
            elif self.period_type == 'WEEKLY':
                self.period_end = self.period_start + timedelta(days=6)
            elif self.period_type == 'MONTHLY':
                # Último dia do mês
                if self.period_start.month == 12:
                    self.period_end = self.period_start.replace(year=self.period_start.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    self.period_end = self.period_start.replace(month=self.period_start.month + 1, day=1) - timedelta(days=1)
            elif self.period_type == 'YEARLY':
                self.period_end = self.period_start.replace(year=self.period_start.year + 1, day=31, month=12)
        
        super().save(*args, **kwargs)


class BudgetCategoryLimit(models.Model):
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='budget_categories_limits',
        db_column='id_budget_id')

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budget_categories_limits',
        db_column='id_category_id')

    limit_amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Budget Category Limit"
        verbose_name_plural = "Budget Category Limits"
        constraints = [
            CheckConstraint(
                condition=Q(limit_amount__gt=0),
                name='limit_amount_positive'
            ),
            models.UniqueConstraint(
                fields=['budget', 'category'],
                name='unique_budget_category'
            )
        ]

    def __str__(self):
        return f"{self.budget.user.email} - {self.category.name}: {self.limit_amount}"

