"""Formulários para gerenciamento de transações."""

from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['user', 'category', 'payment_method', 'amount', 'direction', 'currency', 'occurred_at', 'origin']
        widgets = {
            'occurred_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }