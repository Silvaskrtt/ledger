# backend/users/views.py
"""
Views relacionadas à autenticação e gerenciamento de usuários.
Responsáveis por páginas Web (HTML), não por endpoints de API.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def profile_view(request):
    """
    Página de perfil do usuário autenticado.
    Exibe dados básicos da conta.
    """
    return render(request, 'users/profile.html', {
        'user': request.user
    })
