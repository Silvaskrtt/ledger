import uuid
from django.db.models import Q, F, CheckConstraint
from django.db import models
from django.contrib.auth.models import User
from categories.models import categories
from users.models import users


class budgets(models.Model):
    PERIOD_TYPE_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]

    id_budget = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    
     # Constraints to ensure period_type is either 'monthly', 'quarterly', or 'yearly'
    
    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'period_type', 'period_start'],
                name='unique_budget_period'
            )
        ]
        
    period_start = models.DateField()
    
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='budgets')


class budget_categories_limits(models.Model):
    id_budget = models.ForeignKey(
        budgets,
        on_delete=models.CASCADE,
        related_name='budget_categories_limits')
    
    id_category = models.ForeignKey(
        categories,
        on_delete=models.CASCADE,
        related_name='budget_categories_limits')
    
    limit_amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    class Meta:
        verbose_name = "Budget Category Limit"
        verbose_name_plural = "Budget Category Limits"
        constraints = [
            CheckConstraint(
                condition=Q(limit_amount__gt=0),
                name='limit_amount_positive'
            )
        ]
