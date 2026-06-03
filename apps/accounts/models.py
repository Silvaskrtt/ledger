from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import Group
import os
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from .validators import validate_brazilian_phone, format_brazilian_phone

def avatar_upload_path(instance, filename):
    """Gera caminho único para o avatar"""
    ext = filename.split('.')[-1].lower()
    # Sanitiza o nome do arquivo
    safe_username = ''.join(c for c in instance.user.username if c.isalnum() or c in '._-')
    filename = f"{safe_username}_avatar_{instance.user.id}_{os.urandom(4).hex()}.{ext}"
    return os.path.join('avatars', filename)

def resize_avatar(image, size=(200, 200), quality=85):
    """
    Redimensiona e otimiza a imagem do avatar
    Retorna um ContentFile com a imagem processada
    """
    try:
        # Abrir imagem
        img = Image.open(image)
        
        # Converter para RGB se necessário (remove canal alpha)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Criar fundo branco para transparência
            background = Image.new('RGB', img.size, (138, 79, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calcular dimensões para crop centralizado
        width, height = img.size
        if width != height:
            # Crop para quadrado (pega o centro)
            new_size = min(width, height)
            left = (width - new_size) // 2
            top = (height - new_size) // 2
            right = left + new_size
            bottom = top + new_size
            img = img.crop((left, top, right, bottom))
        
        # Redimensionar para o tamanho desejado
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Criar imagem final com fundo gradiente se necessário
        if img.size != size:
            final_img = Image.new('RGB', size, (138, 79, 255))
            x = (size[0] - img.size[0]) // 2
            y = (size[1] - img.size[1]) // 2
            final_img.paste(img, (x, y))
            img = final_img
        
        # Salvar em memória
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Gerar novo nome
        name, ext = os.path.splitext(os.path.basename(image.name))
        new_name = f"{name}_resized.jpg"
        
        return ContentFile(output.read(), new_name)
    
    except Exception as e:
        print(f"Erro ao redimensionar avatar: {e}")
        return image

class Profile(models.Model):
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('USER', 'Usuário'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def save(self, *args, **kwargs):
        """Ao salvar o perfil, formata o telefone e atualiza o grupo do usuário"""
        # Formata o telefone antes de salvar
        if self.phone:
            self.phone = format_brazilian_phone(self.phone)
        
        # Se avatar foi enviado, redimensiona se o arquivo existir
        if self.avatar and hasattr(self.avatar, 'name') and self.avatar.name:
            try:
                avatar_exists = False
                try:
                    avatar_exists = self.avatar.storage.exists(self.avatar.name)
                except Exception:
                    avatar_path = getattr(self.avatar, 'path', None)
                    avatar_exists = bool(avatar_path and os.path.isfile(avatar_path))

                if not avatar_exists:
                    self.avatar = None
                else:
                    try:
                        if self.avatar.size > 0:
                            resized = resize_avatar(self.avatar)
                            self.avatar = resized
                    except Exception:
                        # Se o arquivo for inválido ou não puder ser lido, descarta o avatar
                        self.avatar = None
            except Exception as e:
                print(f"Erro ao processar avatar: {e}")

        # Primeiro salva o perfil
        super().save(*args, **kwargs)
        # Depois atualiza o grupo
        self.update_user_group()
    
    def update_user_group(self):
        """Atualiza o grupo do usuário baseado na role"""
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
        if self.avatar and hasattr(self.avatar, 'name') and self.avatar.name:
            try:
                if self.avatar.storage.exists(self.avatar.name):
                    return self.avatar.url
            except Exception:
                avatar_path = getattr(self.avatar, 'path', None)
                if avatar_path and os.path.isfile(avatar_path):
                    return self.avatar.url
        return None

    def delete_avatar(self):
        """Remove o arquivo de avatar do sistema de arquivos"""
        if self.avatar and self.avatar.path and os.path.isfile(self.avatar.path):
            try:
                os.remove(self.avatar.path)
                self.avatar = None
                self.save(update_fields=['avatar'])
                return True
            except Exception as e:
                print(f"Erro ao remover avatar: {e}")
                return False
        return False

# Signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria um perfil automaticamente quando um usuário é criado"""
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva o perfil quando o usuário é salvo"""
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
    except Exception as e:
        # Se o avatar estiver quebrado ou faltar arquivo, ignora para não travar o login
        print(f"Erro ao salvar perfil do usuário: {e}")

@receiver(post_delete, sender=Profile)
def delete_avatar_on_profile_delete(sender, instance, **kwargs):
    """Remove o avatar quando o perfil é deletado"""
    if instance.avatar and instance.avatar.path and os.path.isfile(instance.avatar.path):
        try:
            os.remove(instance.avatar.path)
        except Exception as e:
            print(f"Erro ao remover avatar ao deletar perfil: {e}")