import uuid
from django.db import models
from users.models import User
from django.db.models import Q, CheckConstraint


class FinancialGoal(models.Model):
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
        User,
        on_delete=models.CASCADE,
        related_name='financial_goals')

    def __str__(self):
        return f"{self.id_financial_goal} - {self.id_user.email}"