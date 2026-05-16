# reports/models.py
from django.db import models
from django.contrib.auth.models import User

class ReportHistory(models.Model):
    """Histórico de relatórios gerados"""
    
    REPORT_TYPES = [
        ('monthly', 'Relatório Mensal'),
        ('quarterly', 'Relatório Trimestral'),
        ('yearly', 'Relatório Anual'),
        ('custom', 'Personalizado'),
    ]
    
    FORMAT_CHOICES = [
        ('html', 'HTML'),
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='html')
    period_start = models.DateField()
    period_end = models.DateField()
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Relatório'
        verbose_name_plural = 'Relatórios'
    
    def __str__(self):
        return f"{self.user.username} - {self.report_type} - {self.created_at.strftime('%d/%m/%Y')}"