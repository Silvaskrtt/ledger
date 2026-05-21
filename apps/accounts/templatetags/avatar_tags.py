from django import template
from django.utils.safestring import mark_safe
import hashlib

register = template.Library()

@register.simple_tag
def user_avatar(user, size=40, css_class=''):
    """
    Retorna o HTML do avatar do usuário com fallback
    Uso: {% user_avatar user 40 'avatar-class' %}
    """
    if not user.is_authenticated:
        return mark_safe(f'''
            <div class="avatar-fallback {css_class}" style="width: {size}px; height: {size}px;">
                <i class="fas fa-user"></i>
            </div>
        ''')
    
    profile = getattr(user, 'profile', None)
    
    # Se tem avatar
    if profile and profile.avatar and profile.avatar.url:
        return mark_safe(f'''
            <img src="{profile.avatar.url}?t={user.id}" 
                 alt="{user.username}" 
                 class="avatar-img {css_class}" 
                 style="width: {size}px; height: {size}px; object-fit: cover; border-radius: 50%;">
        ''')
    
    # Fallback: iniciais do nome
    name = user.get_full_name() or user.username
    initials = ''.join([part[0].upper() for part in name.split()[:2]])
    
    # Gera cor baseada no username
    hash_obj = hashlib.md5(user.username.encode())
    hash_hex = hash_obj.hexdigest()
    color = f"#{hash_hex[:6]}"
    
    font_size = max(12, size // 2)
    
    return mark_safe(f'''
        <div class="avatar-initials {css_class}" 
             style="width: {size}px; height: {size}px; 
                    background: linear-gradient(135deg, {color}, #8A4FFF);
                    display: flex; align-items: center; justify-content: center; 
                    border-radius: 50%; color: white; font-weight: 600; 
                    font-size: {font_size}px;">
            {initials[:2]}
        </div>
    ''')

@register.filter
def avatar_url(user):
    """Retorna a URL do avatar ou None"""
    if not user.is_authenticated:
        return None
    
    profile = getattr(user, 'profile', None)
    if profile and profile.avatar:
        return profile.avatar.url
    
    return None

@register.simple_tag
def avatar_exists(user):
    """Verifica se o usuário tem avatar"""
    if not user.is_authenticated:
        return False
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.avatar)