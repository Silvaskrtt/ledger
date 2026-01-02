# backend/users/views.py
"""Views para autenticação e gerenciamento de usuários."""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def home(request):
    """Página inicial após login."""
    if request.user.is_authenticated:
        # Se já está logado, vai para home
        user_name = request.user.get_full_name() or request.user.username
        return render(request, 'home/home.html', {
            'user_name': user_name
        })
    else:
        # Se não está logado, redireciona para login
        return redirect('account_login')
    
@login_required
def profile_view(request):
    """Página de perfil do usuário."""
    return render(request, 'users/profile.html', {
        'user': request.user
    })