from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserForm(forms.ModelForm):
    """Form para dados do User"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl input-field text-slate-100'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl input-field text-slate-100'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl input-field text-slate-100', 'readonly': 'readonly'}),
        }

class UserProfileForm(forms.ModelForm):
    """Form para dados do Profile"""
    class Meta:
        model = Profile
        fields = ['role', 'phone']
        widgets = {
            'role': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl input-field text-slate-100'}),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl input-field text-slate-100',
                'placeholder': '(11) 99999-9999'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna o campo role somente leitura se não for admin
        if self.instance and self.instance.user:
            if not self.instance.user.is_superuser and self.instance.role != 'ADMIN':
                self.fields['role'].disabled = True