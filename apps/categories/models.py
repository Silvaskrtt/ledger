# categories/models.py
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    
    TYPE_CHOICES = [
        ('income', 'Entrada'),
        ('expense', 'Saída'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=10,
        default='expense',
        choices=TYPE_CHOICES,
        help_text='Tipo da categoria: Entrada ou Saída'
    )
    
    icon = models.CharField(
        max_length=50,
        default='📌',
        blank=True,
        help_text="Emoji ou ícone para representar a categoria"
    )
    
    color = models.CharField(
        max_length=20,
        default='#8A4FFF',
        blank=True,
        help_text="Cor hexadecimal para identificar a categoria"
    )
    
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Orçamento mensal para esta categoria (opcional)"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']  # Evitar categorias duplicadas por usuário
    
    def __str__(self):
        return f"{self.icon} {self.name}"
    
    def get_total_spent(self, year=None, month=None):
        """Calcula total gasto nesta categoria"""
        from transactions.models import Transaction
        queryset = Transaction.objects.filter(
            user=self.user,
            category=self,
            type='expense'
        )
        
        if year and month:
            queryset = queryset.filter(
                date__year=year,
                date__month=month
            )
        elif year:
            queryset = queryset.filter(date__year=year)
        
        return queryset.aggregate(total=models.Sum('amount'))['total'] or 0