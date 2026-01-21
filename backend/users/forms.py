# users/forms.py
from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model
import re
import uuid

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30, 
        label='Nome', 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Seu nome',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        label='Sobrenome', 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Seu sobrenome',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar email não obrigatório temporariamente para desenvolvimento
        self.fields['email'].required = False
        
        # Configurar campo username como opcional
        if 'username' in self.fields:
            self.fields['username'].required = False
            self.fields['username'].widget.attrs.update({
                'placeholder': 'Nome de usuário (opcional)',
                'class': 'form-control'
            })
        
        # Ajustar labels e placeholders
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Digite seu e-mail (opcional para desenvolvimento)',
            'class': 'form-control'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Digite sua senha',
            'class': 'form-control'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirme sua senha',
            'class': 'form-control'
        })
    
    def generate_username(self, email=None):
        """Gera um username único"""
        if email:
            # Tenta usar o email
            base_username = email.split('@')[0]
            base_username = re.sub(r'[^\w]', '_', base_username)
            base_username = base_username.lower()
            base_username = re.sub(r'_+', '_', base_username)
            base_username = base_username.strip('_')
            
            if base_username and base_username[0].isdigit():
                base_username = 'user_' + base_username
            
            if not base_username or len(base_username) < 3:
                base_username = 'user'
        else:
            base_username = 'user'
        
        # Verifica unicidade
        User = get_user_model()
        username = base_username
        counter = 1
        original_username = base_username
        
        while User.objects.filter(username=username).exists():
            username = f"{original_username}_{counter}"
            counter += 1
            if counter > 100:
                username = f"user_{uuid.uuid4().hex[:8]}"
                break
        
        return username
    
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        
        # Se forneceu username, valida
        if username:
            if len(username) < 3:
                raise forms.ValidationError('Mínimo 3 caracteres.')
            if len(username) > 150:
                raise forms.ValidationError('Máximo 150 caracteres.')
            if not re.match(r'^[\w.@+-]+$', username):
                raise forms.ValidationError('Caracteres inválidos.')
            
            # Verifica se já existe
            User = get_user_model()
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError('Username já em uso.')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        
        # Para desenvolvimento, aceita email vazio
        if not email:
            return f"dev_{uuid.uuid4().hex[:8]}@example.com"  # Email placeholder
        
        return email
    
    def save(self, request):
        # Se não tem username, gera um
        username = self.cleaned_data.get('username')
        if not username:
            email = self.cleaned_data.get('email', '')
            username = self.generate_username(email if email else None)
            self.cleaned_data['username'] = username
        
        # Cria o usuário
        user = super().save(request)
        
        # Atualiza campos adicionais
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        
        return user