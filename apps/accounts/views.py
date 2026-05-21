import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.files.base import ContentFile
from .models import Profile
from .forms import UserProfileForm, UserForm
import os
from PIL import Image
from io import BytesIO

@login_required
def get_user_data(request):
    """Retorna dados atualizados do usuário via JSON"""
    user = request.user
    profile = user.profile
    
    return JsonResponse({
        'name': f"{user.first_name} {user.last_name}".strip(),
        'email': user.email,
        'phone': profile.phone if profile.phone else 'Não informado',
        'member_since': user.date_joined.strftime('%d/%m/%Y'),
        'avatar_url': profile.get_avatar_url()
    })

@require_POST
@login_required
def profile_update_ajax(request):
    """Atualiza nome ou telefone via AJAX (JSON)"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados inválidos'}, status=400)

    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if 'name' in data:
        full_name = data['name'].strip()
        if len(full_name) < 3:
            return JsonResponse({'success': False, 'error': 'Nome muito curto'})
        # Divide em first_name e last_name
        parts = full_name.split(maxsplit=1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''
        user.save()
        return JsonResponse({'success': True})

    if 'phone' in data:
        profile.phone = data['phone'].strip()
        profile.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Campo inválido'}, status=400)

@login_required
def profile_view(request):
    """View do perfil do usuário"""
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        # Se não existir perfil, cria um (fallback)
        profile = Profile.objects.create(user=user)
    
    user_form = UserForm(instance=user)
    profile_form = UserProfileForm(instance=profile)
    password_form = PasswordChangeForm(user)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'account/profile.html', context)

@login_required
def profile_update(request):
    """Atualiza os dados do perfil"""
    if request.method == 'POST':
        user = request.user
        profile = user.profile
        
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Erro ao atualizar perfil. Verifique os dados.')
    
    return redirect('accounts:profile')

@require_POST
@login_required
def avatar_upload(request):
    """View para upload de avatar via AJAX com redimensionamento"""
    try:
        if not request.FILES.get('avatar'):
            return JsonResponse({'success': False, 'error': 'Nenhuma imagem selecionada'}, status=400)
        
        avatar = request.FILES['avatar']
        profile = request.user.profile
        
        # Validações básicas
        max_size = 5 * 1024 * 1024  # 5MB
        if avatar.size > max_size:
            return JsonResponse({'success': False, 'error': 'A imagem não pode ter mais que 5MB'})
        
        # Valida tipo de arquivo
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        file_extension = avatar.name.split('.')[-1].lower()
        
        if avatar.content_type not in allowed_types and file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            return JsonResponse({'success': False, 'error': 'Formato de imagem não permitido. Use JPEG, PNG, GIF ou WEBP'})
        
        # Remove avatar antigo se existir
        if profile.avatar:
            profile.delete_avatar()
        
        # Salva novo avatar (o redimensionamento ocorre no save do model)
        profile.avatar = avatar
        profile.save()
        
        return JsonResponse({
            'success': True,
            'avatar_url': profile.get_avatar_url(),
            'message': 'Avatar atualizado com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro ao fazer upload: {str(e)}'}, status=500)

@require_POST
@login_required
def avatar_remove(request):
    """Remove o avatar do usuário via AJAX"""
    try:
        profile = request.user.profile
        
        if profile.delete_avatar():
            return JsonResponse({
                'success': True,
                'message': 'Avatar removido com sucesso!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Não foi possível remover o avatar'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro ao remover avatar: {str(e)}'}, status=500)

@login_required
def password_change(request):
    """Altera a senha do usuário"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mantém o usuário logado após trocar a senha
            update_session_auth_hash(request, user)
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Erro ao alterar senha. Verifique os dados.')
    
    return redirect('accounts:profile')