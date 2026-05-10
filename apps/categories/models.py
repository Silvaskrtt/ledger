from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    
    TYPE_CHOICES = [
        ('income', 'Entrada'),    # Income
        ('expense', 'Saída'),     # Expense
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=10,
        default='income',
        choices=TYPE_CHOICES,
        help_text='Tipo da categoria: Entrada ou Saída'
    )
    
    icon = models.CharField(
        max_length=50,
        default='receipt',
        blank=True,
        help_text="Nome do ícone (Font Awesome, Material Icons, etc.)"
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name