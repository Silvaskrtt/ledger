# backend/users/views.py
"""
Views relacionadas à autenticação e gerenciamento de usuários.
Responsáveis por páginas Web (HTML), não por endpoints de API.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def home(request):
    """
    Página inicial do usuário autenticado.
    Renderiza a home após login com informações básicas do usuário.
    """
    # Garante nome amigável para exibição
    user_name = request.user.get_full_name() or request.user.username

    return render(request, 'home/home.html', {
        'user_name': user_name
    })


@login_required
def profile_view(request):
    """
    Página de perfil do usuário autenticado.
    Exibe dados básicos da conta.
    """
    return render(request, 'users/profile.html', {
        'user': request.user
    })
