# import_export/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
import json

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
    """Histórico de importações realizadas com detalhes de banco e formato"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('completed_with_errors', 'Concluído com Erros'),
        ('failed', 'Falhou'),
    ]
    
    BANK_CHOICES = [
        ('bb', 'Banco do Brasil'),
        ('itau', 'Itaú'),
        ('nubank', 'Nubank'),
        ('generic', 'Genérico'),
    ]
    
    FILE_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF'),
        ('ofx', 'OFX'),
        ('bbt', 'BBT (Banco do Brasil)'),
        ('txt', 'TXT'),
        ('json', 'JSON'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='imports')
    filename = models.CharField(max_length=255)
    bank = models.CharField(max_length=20, choices=BANK_CHOICES, default='generic')
    file_format = models.CharField(max_length=10, choices=FILE_FORMAT_CHOICES)
    
    # Estatísticas de importação
    total_lines_read = models.IntegerField(default=0, help_text="Total de linhas/registros lidos do arquivo")
    records_imported = models.IntegerField(default=0, help_text="Transações salvas com sucesso")
    records_failed = models.IntegerField(default=0, help_text="Transações com erro de validação")
    duplicates_ignored = models.IntegerField(default=0, help_text="Registros duplicados ignorados")
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True, help_text="Descrição do erro geral")
    
    # Detalhes de validação
    validation_errors = models.JSONField(default=list, blank=True, help_text="Lista de erros por linha")
    
    # Período do extrato (opcional)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    
    # Metadados
    file_size = models.BigIntegerField(default=0, help_text="Tamanho do arquivo em bytes")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Importação'
        verbose_name_plural = 'Importações'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_bank_display()} ({self.get_file_format_display()}) - {self.status}"
    
    def add_validation_error(self, line_number, error_message, raw_data=None):
        """Adiciona um erro de validação ao histórico"""
        if not self.validation_errors:
            self.validation_errors = []
        self.validation_errors.append({
            'line': line_number,
            'error': error_message,
            'data': str(raw_data)[:500] if raw_data else None
        })

class TransactionImportMetadata(models.Model):
    """Metadados da importação para cada transação"""
    
    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='import_metadata'
    )
    import_history = models.ForeignKey(
        ImportHistory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imported_transactions'
    )
    
    # Identificadores únicos do banco
    fitid = models.CharField(max_length=255, blank=True, null=True, help_text="FITID do OFX ou identificador único do banco")
    document_number = models.CharField(max_length=255, blank=True, null=True, help_text="Número do documento/lançamento")
    
    # Tipos de transação
    TRANSACTION_TYPE_CHOICES = [
        ('credit', 'Crédito'),
        ('debit', 'Débito'),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, blank=True)
    
    # Dados do extrato
    previous_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Banco de origem
    bank = models.CharField(max_length=50, blank=True)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Rastreabilidade
    raw_data = models.JSONField(default=dict, blank=True, help_text="Dados brutos originais do arquivo")
    import_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Metadados de Importação'
        verbose_name_plural = 'Metadados de Importação'
        indexes = [
            models.Index(fields=['fitid']),
            models.Index(fields=['document_number']),
            models.Index(fields=['import_history']),
        ]
    
    def __str__(self):
        return f"Importação - {self.transaction.description} ({self.bank})"