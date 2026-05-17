# import_export/forms.py
"""
Formulários para importação de extratos bancários
"""
from django import forms
from .models import ImportHistory


class BankStatementImportForm(forms.Form):
    """Formulário para importação de extratos bancários"""
    
    BANK_CHOICES = [
        ('', '--- Selecione um banco ---'),
        ('bb', 'Banco do Brasil'),
        ('itau', 'Itaú'),
        ('nubank', 'Nubank'),
    ]
    
    FILE_FORMAT_CHOICES = [
        ('', '--- Selecione o formato ---'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel (XLSX)'),
        ('pdf', 'PDF'),
        ('ofx', 'OFX'),
        ('bbt', 'BBT (Banco do Brasil)'),
        ('txt', 'TXT'),
    ]
    
    bank = forms.ChoiceField(
        choices=BANK_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True,
            'id': 'import-bank'
        }),
        label='Banco'
    )
    
    file_format = forms.ChoiceField(
        choices=FILE_FORMAT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True,
            'id': 'import-format'
        }),
        label='Formato do Arquivo'
    )
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls,.pdf,.ofx,.bbt,.txt',
            'required': True,
            'id': 'import-file'
        }),
        label='Arquivo'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        bank = cleaned_data.get('bank')
        file_format = cleaned_data.get('file_format')
        file = cleaned_data.get('file')
        
        if not bank:
            self.add_error('bank', 'Selecione um banco')
        
        if not file_format:
            self.add_error('file_format', 'Selecione um formato')
        
        if not file:
            self.add_error('file', 'Selecione um arquivo')
        
        # Validar extensão do arquivo
        if file:
            filename = file.name.lower()
            extension = filename.split('.')[-1] if '.' in filename else ''
            
            valid_extensions = {
                'csv': ['csv'],
                'xlsx': ['xlsx', 'xls'],
                'pdf': ['pdf'],
                'ofx': ['ofx'],
                'bbt': ['bbt'],
                'txt': ['txt'],
            }
            
            if file_format and file_format not in valid_extensions:
                self.add_error('file_format', 'Formato inválido')
            elif file_format and extension not in valid_extensions.get(file_format, []):
                self.add_error('file', f'Extensão do arquivo ({extension}) não corresponde ao formato selecionado ({file_format})')
            
            # Validar tamanho (máximo 10MB)
            if file.size > 10 * 1024 * 1024:
                self.add_error('file', 'Arquivo muito grande (máximo 10MB)')
        
        return cleaned_data
