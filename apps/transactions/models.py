from django.db import models
from django.contrib.auth.models import User
from categories.models import Category

class Transaction(models.Model):
    
    TYPE_CHOICES = Category.TYPE_CHOICES
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.CharField('Categoria', max_length=50)  
    amount = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    description = models.CharField('Descrição', max_length=200)
    type = models.CharField(max_length=10, choices=Category.TYPE_CHOICES) 
    date = models.DateField('Data')
    notes = models.TextField('Observações', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - R$ {self.amount} - {self.date}"