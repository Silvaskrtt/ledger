from django import forms
from .models import Transaction
from categories.models import Category

class TransactionForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        empty_label="Selecione uma categoria",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Categoria'
    )
    
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'date', 'description', 'type', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'amount': 'Valor (R$)',
            'date': 'Data',
            'description': 'Descrição',
            'type': 'Tipo',
            'notes': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)