import uuid
from django.utils import timezone
from django.db.models import Q, CheckConstraint
from django.db import models
from accounts.models import Account
from users.models import User
from categories.models import Category


class PaymentMethod(models.Model):
    TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('PIX', 'Pix'),
        ('CASH', 'Cash'),
    ]
    
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='PIX'
        )
    
    id_payment_method = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    description = models.CharField(max_length=100, null=True, blank=True)
    requires_account = models.BooleanField(default=True)
    allows_installments = models.BooleanField(default=True)
    id_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='payment_methods')
    
    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'type', 'description'],
                name='unique_payment_method_per_user'
            )
        ]


class InstallmentPlan(models.Model):
    id_installment_plan = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    # Constraints to ensure total_amount is positive and below a certain limit
    class Meta:
        verbose_name = "Installment Plan"
        verbose_name_plural = "Installment Plans"
        constraints = [
            CheckConstraint(condition=Q(total_amount__gt=0), name='total_amount_positive'),
            CheckConstraint(condition=Q(total_amount__lt=10000), name='total_amount_max_limit'),
            CheckConstraint(condition=Q(installments__gt=0), name='installments_positive'),
            CheckConstraint(condition=Q(installments__lte=36), name='installments_max_limit'),
        ]
        
    def __str__(self):
        return f"Total: {self.total_amount}"
    
    installments = models.IntegerField()   
    start_date = models.DateField(default=timezone.now)
    
    id_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='installment_plans')

    id_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='installment_plans')

    id_category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='installment_plans')