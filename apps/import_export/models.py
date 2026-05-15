# import_export/models.py
from django.db import models
from django.contrib.auth.models import User

class ExportHistory(models.Model):
    """Histórico de exportações realizadas"""
    
    FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exports')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    file_size = models.BigIntegerField(default=0, help_text="Tamanho do arquivo em bytes")
    records_count = models.IntegerField(default=0, help_text="Número de registros exportados")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Exportação'
        verbose_name_plural = 'Exportações'
    
    def __str__(self):
        return f"{self.user.username} - {self.format} - {self.created_at}"

class ImportHistory(models.Model):
    """Histórico de importações realizadas"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='imports')
    filename = models.CharField(max_length=255)
    format = models.CharField(max_length=10)
    records_imported = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Importação'
        verbose_name_plural = 'Importações'
    
    def __str__(self):
        return f"{self.user.username} - {self.filename} - {self.status}"