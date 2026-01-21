# users/signals.py
from django.db.models.signals import pre_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
import re
import uuid

User = get_user_model()

@receiver(pre_save, sender=User)
def ensure_user_has_username(sender, instance, **kwargs):
    """Garante que todos os usuários tenham um username válido"""
    if not instance.username or instance.username.strip() == '':
        # Gera username baseado no email
        if instance.email:
            base_username = instance.email.split('@')[0]
            base_username = re.sub(r'[^\w]', '_', base_username)
            base_username = base_username.lower()
            base_username = re.sub(r'_+', '_', base_username)
            base_username = base_username.strip('_')
            
            if not base_username or len(base_username) < 3:
                base_username = 'user'
            
            username = base_username
            counter = 1
            original_username = base_username
            
            while User.objects.filter(username=username).exclude(pk=instance.pk).exists():
                username = f"{original_username}_{counter}"
                counter += 1
                if counter > 100:
                    username = f"user_{uuid.uuid4().hex[:8]}"
                    break
        else:
            username = f"user_{uuid.uuid4().hex[:8]}"
        
        instance.username = username