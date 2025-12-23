import uuid
from django.db import models
from django.contrib.auth.models import User
from categories.models import categories
from users.models import users
from payments.models import payment_methods
from accounts.models import accounts
from django.db.models import Q, CheckConstraint


class recurrence_rules(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Biweekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]

    DIRECTION_CHOICES = [
        ('IN', 'Income'),
        ('OUT', 'Expense'),
    ]

    id_recurrence_rule = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    id_recurrence_rule = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES)
    next_execution = models.DateField()
    max_executions = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Recurrence Rule"
        verbose_name_plural = "Recurrence Rules"
        constraints = [
            CheckConstraint(
                condition=Q(max_executions__gt=0),
                name='max_executions_positive'
            )
        ]
    
    executions_count = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    direction = models.CharField(max_length=50, choices=DIRECTION_CHOICES)
    
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='recurrence_rules')
    
    id_category = models.ForeignKey(
        categories,
        on_delete=models.CASCADE,
        related_name='recurrence_rules')
    
    id_payment_method = models.ForeignKey(
        payment_methods,
        on_delete=models.CASCADE,
        related_name='recurrence_rules')
    
    id_account = models.ForeignKey(
        accounts,
        on_delete=models.CASCADE,
        related_name='recurrence_rules')