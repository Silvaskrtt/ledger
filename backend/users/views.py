"""Views para autenticação e gerenciamento de usuários."""

from .models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def login_view(request):
    """View para login de usuários."""
    if request.method == 'POST':
        # Lógica de autenticação
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Credenciais inválidas'}) # Não tem front ainda
        
    return render(request, 'login.html') # Não tem front ainda

@login_required
def logout_view(request):
    """View para logout de usuários."""
    logout(request)
    return redirect('login') # Não tem front ainda

def register_view(request):
    """View para registro de novos usuários."""
    if request.method == 'POST':
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if not name or not surname or not email or not password:
            return render(request, 'register.html', {'error': 'Todos os campos são obrigatórios'}) # Não tem front ainda
        
        if password != password_confirm:
            return render(request, 'register.html', {'error': 'As senhas não coincidem'}) # Não tem front ainda
        
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email já registrado'}) # Não tem front ainda
        
        # Lógica para criar um novo usuário
        user = User.objects.create(
            name=name, 
            surname=surname, 
            email=email, 
            password=password)
        user.set_password(password)  # Hash da senha
        user.save()
        
        return redirect('login')  # Não tem front ainda