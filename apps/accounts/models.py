from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
import os
from .validators import validate_brazilian_phone, format_brazilian_phone

def avatar_upload_path(instance, filename):
    """Gera caminho único para o avatar"""
    ext = filename.split('.')[-1]
    filename = f"{instance.user.username}_avatar_{instance.user.id}.{ext}"
    return os.path.join('avatars', filename)

class Profile(models.Model):
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('USER', 'Usuário'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='USER'
        )
    
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        null=True,
        blank=True,
        verbose_name='Avatar'
    )
    phone = models.CharField(
        max_length=20, 
        blank=True,
        null=True,
        verbose_name='Telefone',
        validators=[validate_brazilian_phone],
        help_text='Formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX'
        )
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def save(self, *args, **kwargs):
        """Ao salvar o perfil, formata o telefone e atualiza o grupo do usuário"""
        # Formata o telefone antes de salvar
        if self.phone:
            self.phone = format_brazilian_phone(self.phone)
        
        # Primeiro salva o perfil
        super().save(*args, **kwargs)
        # Depois atualiza o grupo (sem salvar o user)
        self.update_user_group()
    
    def update_user_group(self):
        """Atualiza o grupo do usuário baseado na role"""
        
        # Determina qual grupo deve ter baseado na role
        grupo_destino = None
        if self.role == 'ADMIN':
            grupo_destino = 'Administradores'
        elif self.role == 'USER':
            grupo_destino = 'Usuários'
        
        if grupo_destino:
            try:
                # Remove de todos os grupos primeiro
                self.user.groups.clear()
                # Adiciona ao grupo correto
                grupo = Group.objects.get(name=grupo_destino)
                self.user.groups.add(grupo)
            except Group.DoesNotExist:
                pass

    def get_avatar_url(self):
        """Retorna URL do avatar ou None"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None

    def delete_avatar(self):
        """Remove o arquivo de avatar do sistema de arquivos"""
        if self.avatar and self.avatar.path and os.path.isfile(self.avatar.path):
            os.remove(self.avatar.path)
            self.avatar = None
            self.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria um perfil automaticamente quando um usuário é criado"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva o perfil quando o usuário é salvo"""
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

@receiver(models.signals.post_delete, sender=Profile)
def delete_avatar_on_profile_delete(sender, instance, **kwargs):
    """Remove o avatar quando o perfil é deletado"""
    if instance.avatar and instance.avatar.path and os.path.isfile(instance.avatar.path):
        os.remove(instance.avatar.path)