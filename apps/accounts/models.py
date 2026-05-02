from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
import os

def avatar_upload_path(istance, filename):
    """Gera caminho único para o avatar"""
    ext = filename.split('.')[-1]
    filename = f" {instance.user.username}_avatar.{ext}"
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
        verbose_name='Telefone'
        )
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def save(self, *args, **kwargs):
        """Ao salvar o perfil, atualiza o grupo do usuário"""
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