from django import forms
from .models import Goal

class GoalForm(forms.ModelForm):
    """Formulário para criação/edição de metas"""
    
    class Meta:
        model = Goal
        fields = ['title', 'description', 'target', 'current', 'deadline', 'icon']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Viagem dos sonhos, Carro novo...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Descreva sua meta (opcional)...'
            }),
            'target': forms.NumberInput(attrs={
                'class': 'form-input target-input',
                'placeholder': 'R$ 0,00',
                'step': '0.01'
            }),
            'current': forms.NumberInput(attrs={
                'class': 'form-input current-input',
                'placeholder': 'R$ 0,00',
                'step': '0.01'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'icon': forms.HiddenInput()
        }
    
    def clean_target(self):
        target = self.cleaned_data.get('target')
        if target <= 0:
            raise forms.ValidationError('O valor alvo deve ser maior que zero.')
        return target
    
    def clean_current(self):
        current = self.cleaned_data.get('current', 0)
        if current < 0:
            raise forms.ValidationError('O valor atual não pode ser negativo.')
        return current
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        from django.utils import timezone
        if deadline and deadline < timezone.now().date():
            raise forms.ValidationError('A data limite não pode ser anterior à data atual.')
        return deadline