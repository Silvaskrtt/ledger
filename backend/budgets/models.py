import uuid
from django.db import models
from django.db.models import CheckConstraint, Q
from users.models import User
from categories.models import Category


class Budget(models.Model):
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
    id_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budgets')
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    period_start = models.DateField()

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'period_type', 'period_start'],
                name='unique_budget_period'
            )
        ]

    def __str__(self):
        return f"Budget {self.period_type} - {self.id_user.email}"


class BudgetCategoryLimit(models.Model):
    id_budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='budget_categories_limits')

    id_category = models.ForeignKey(
        Category,
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

    def __str__(self):
        return f"{self.id_budget.id_user.email} - {self.id_category.name}: {self.limit_amount}"
