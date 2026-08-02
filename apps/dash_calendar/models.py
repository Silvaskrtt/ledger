from django.conf import settings
from django.db import models


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('expense', 'Despesa'),
        ('income', 'Receita'),
        ('saving', 'Economia'),
        ('card', 'Cartão'),
    ]

    RECURRENCE_CHOICES = [
        ('none', 'Não repetir'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
        ('yearly', 'Anual'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_transactions'
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    tag = models.CharField(max_length=50, blank=True, default='')
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default='none')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transação do Calendário'
        verbose_name_plural = 'Transações do Calendário'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'type']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} - R$ {self.amount} - {self.date}"


class MonthlyBudget(models.Model):
    """Planejamento mensal de orçamento"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_budgets'
    )
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    
    categories = models.JSONField(default=dict)
    extras = models.JSONField(default=list)
    total_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    divisor = models.IntegerField(default=30)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Planejamento Mensal'
        verbose_name_plural = 'Planejamentos Mensais'
        unique_together = ['user', 'year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year} - R$ {self.total_planned}"

    def get_daily_goal(self):
        """Retorna o valor diário baseado no total planejado e no divisor"""
        if self.divisor > 0:
            return float(self.total_planned) / self.divisor
        return 0