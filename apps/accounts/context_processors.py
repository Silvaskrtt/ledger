def user_avatar_context(request):
    """
    Versão simplificada que não acessa diretamente o perfil
    """
    context = {
        'user_avatar_url': None,
        'user_has_avatar': False,
        'user_avatar_initials': '',
        'user_avatar_color': '#8A4FFF'
    }
    
    if request.user.is_authenticated:
        try:
            # Usa hasattr para evitar erro se o perfil não existir
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                if profile and hasattr(profile, 'avatar'):
                    context['user_avatar_url'] = profile.avatar.url if profile.avatar else None
                    context['user_has_avatar'] = bool(profile.avatar)
            
            # Gerar iniciais mesmo sem perfil
            name = request.user.get_full_name() or request.user.username
            initials = ''.join([part[0].upper() for part in name.split()[:2]])
            context['user_avatar_initials'] = initials[:2] if initials else request.user.username[0].upper()
            
        except Exception:
            pass
    
    return context