# backend/budgets/models.py
from decimal import Decimal
import uuid
from datetime import timedelta, date, datetime
from django.db import models
from django.db.models import CheckConstraint, Q, Sum
from django.contrib.auth.models import User
from django.utils.timezone import now, make_aware
from categories.models import Category
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

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
    period_end = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

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
            models.Index(fields=['user', 'period_type', 'period_start']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_period_type_display()} {self.period_start.strftime('%B %Y')}"
    
    def clean(self):
        """Validação adicional"""
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError('A data final não pode ser anterior à data inicial.')
    
    def save(self, *args, **kwargs):
        """Calcular period_end automaticamente se não informado."""
        self.clean()
        
        if not self.period_end:
            if self.period_type == 'DAILY':
                self.period_end = self.period_start
            elif self.period_type == 'WEEKLY':
                self.period_end = self.period_start + timedelta(days=6)
            elif self.period_type == 'MONTHLY':
                # Último dia do mês
                if self.period_start.month == 12:
                    self.period_end = self.period_start.replace(
                        year=self.period_start.year + 1, 
                        month=1, 
                        day=1
                    ) - timedelta(days=1)
                else:
                    self.period_end = self.period_start.replace(
                        month=self.period_start.month + 1, 
                        day=1
                    ) - timedelta(days=1)
            elif self.period_type == 'YEARLY':
                self.period_end = self.period_start.replace(
                    year=self.period_start.year + 1, 
                    day=31, 
                    month=12
                )
        
        super().save(*args, **kwargs)
    
    def update_status(self):
        """Atualiza o status do orçamento baseado nos gastos"""
        from transactions.models import Transaction
        
        # Calcular total gasto
        total_spent = self.calculate_total_spent()
        
        # Calcular total do orçamento
        total_budget = self.calculate_total_budget()
        
        if total_spent >= total_budget:
            self.status = 'EXCEEDED'
        elif total_spent >= total_budget * 0.9:  # 90% ou mais
            self.status = 'ACTIVE'  # Mantém ativo, mas próximo do limite
        else:
            self.status = 'ACTIVE'
        
        # Verificar se expirou
        if self.period_end and self.period_end < date.today():
            self.status = 'EXPIRED'
        
        self.save()
    
    def calculate_total_spent(self):
        """Calcula o total gasto no período - USAR occurred_at"""
        from transactions.models import Transaction
        
        # Criar datetimes com timezone para comparação
        start_datetime = make_aware(datetime.combine(self.period_start, datetime.min.time()))
        
        if self.period_end:
            end_datetime = make_aware(datetime.combine(self.period_end, datetime.max.time()))
        
        # Query com occurred_at
        spent = Transaction.objects.filter(
            user=self.user,
            occurred_at__gte=start_datetime,
            direction='OUT',
            is_deleted=False
        )
        
        if self.period_end:
            spent = spent.filter(occurred_at__lte=end_datetime)
        
        total = spent.aggregate(total=Sum('amount'))['total'] or 0
        
        return float(total)
    
    def calculate_total_budget(self):
        """Calcula o total orçado"""
        return self.budget_categories_limits.aggregate(
            total=Sum('limit_amount')
        )['total'] or 0


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

    limit_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])

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
        return f"{self.category.name}: R$ {self.limit_amount}"
    
    def clean(self):
        """Validação adicional"""
        if self.limit_amount <= 0:
            raise ValidationError('O valor do limite deve ser maior que zero.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Atualizar status do orçamento
        if self.budget:
            self.budget.update_status()