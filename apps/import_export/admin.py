from django.contrib import admin
from .models import ExportHistory, ImportHistory, TransactionImportMetadata


@admin.register(ExportHistory)
class ExportHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'format', 'records_count', 'file_size', 'created_at']
    list_filter = ['format', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(ImportHistory)
class ImportHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'filename', 'bank', 'file_format', 'status', 'records_imported', 'records_failed', 'created_at']
    list_filter = ['status', 'bank', 'file_format', 'created_at']
    search_fields = ['user__username', 'filename']
    readonly_fields = ['created_at', 'completed_at', 'validation_errors']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('user', 'filename', 'bank', 'file_format', 'file_size')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Estatísticas', {
            'fields': ('total_lines_read', 'records_imported', 'records_failed', 'duplicates_ignored')
        }),
        ('Período', {
            'fields': ('period_start', 'period_end'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Erros', {
            'fields': ('validation_errors',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TransactionImportMetadata)
class TransactionImportMetadataAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'bank', 'fitid', 'document_number', 'transaction_type', 'import_date']
    list_filter = ['bank', 'transaction_type', 'import_date']
    search_fields = ['fitid', 'document_number', 'transaction__description']
    readonly_fields = ['import_date', 'raw_data']
    ordering = ['-import_date']
    
    fieldsets = (
        ('Transação', {
            'fields': ('transaction', 'import_history')
        }),
        ('Identificadores', {
            'fields': ('fitid', 'document_number')
        }),
        ('Detalhes Bancários', {
            'fields': ('bank', 'account_number', 'transaction_type')
        }),
        ('Saldos', {
            'fields': ('previous_balance', 'current_balance'),
            'classes': ('collapse',)
        }),
        ('Rastreabilidade', {
            'fields': ('import_date', 'raw_data'),
            'classes': ('collapse',)
        }),
    )

