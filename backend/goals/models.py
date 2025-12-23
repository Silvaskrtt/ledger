import uuid
from django.db import models
from django.contrib.auth.models import User
from users.models import users
from django.db.models import Q, F, CheckConstraint


class financial_goals(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

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
   
    id_financial_goal = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    class Meta:
        verbose_name = "Financial Goal"
        verbose_name_plural = "Financial Goals"
        constraints = [
            CheckConstraint(
                condition=Q(target_amount__gt=0),
                name='target_amount_positive'
            )
        ]
    
    deadline = models.DateField()
    strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='financial_goals')