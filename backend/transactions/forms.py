"""Formulários para gerenciamento de transações."""

from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['id_user', 'id_category', 'id_payment_method', 'amount', 'direction', 'currency', 'occurred_at', 'origin']