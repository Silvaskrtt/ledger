# backend/accounts/models.py

import uuid
from django.db import models
from django.conf import settings

class Account(models.Model):
    TYPE_CHOICES = [
        ('CHECKING', 'Conta Corrente'),
        ('SAVINGS', 'Conta Poupança'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('INVESTMENT', 'Investimentos'),
        ('CASH', 'Dinheiro'),
        ('OTHER', 'Outro'),
    ]
    
    id_account = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='CHECKING'
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        ordering = ['-created_at']
