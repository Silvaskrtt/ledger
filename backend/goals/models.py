# backend/goals/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, CheckConstraint
from django.utils.timezone import now
from datetime import date
class FinancialGoal(models.Model):
    STRATEGY_CHOICES = [
        ('SAVE', 'Save'),
        ('INVEST', 'Invest'),
        ('SPEND', 'Spend'),
        ('DEBT_PAYOFF', 'Debt Payoff')
    ]

    id_financial_goal = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    id_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='financial_goals'
    )

    name = models.CharField(max_length=120)

    is_cancelled = models.BooleanField(default=False)

    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    deadline = models.DateField()
    strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES)

    created_at = models.DateTimeField(
        default=now,
        editable=False,
        db_index=True
    )

    class Meta:
        verbose_name = "Financial Goal"
        verbose_name_plural = "Financial Goals"
        constraints = [
            CheckConstraint(
                condition=Q(target_amount__gt=0),
                name='target_amount_positive'
            )
        ]
        indexes = [
            models.Index(fields=['id_user', 'deadline']),
        ]

    def __str__(self):
        return f"{self.id_financial_goal} - {self.id_user.email}"


    @property
    def status(self):
        if self.is_cancelled:
            return 'CANCELLED'
        if self.current_amount >= self.target_amount:
            return 'COMPLETED'
        if self.deadline < date.today():
            return 'EXPIRED'
        return 'ACTIVE'

    @property
    def percent(self):
        if self.target_amount == 0:
            return 0
        return min((self.current_amount / self.target_amount) * 100, 100)
