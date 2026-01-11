# backend/payments/signals.py

from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from .models import PaymentMethod
from .defaults import create_default_payment_methods_for_user
from .defaults import DEFAULT_PAYMENT_METHODS
import uuid
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_payment_methods(sender, instance, created, **kwargs):
    """
    Cria métodos de pagamento padrão quando um novo usuário é criado.
    """
    if created:
        try:
            # Cria cada método padrão
            for method_data in DEFAULT_PAYMENT_METHODS:
                # Remove campos extras que não estão no modelo
                method_data_copy = {k: v for k, v in method_data.items() 
                                   if k in ['type', 'description', 'requires_account', 'allows_installments']}
                
                PaymentMethod.objects.create(
                    id_payment_method=uuid.uuid4(),
                    id_user=instance,
                    **method_data_copy
                )
            
            logger.info(f"Métodos de pagamento padrão criados para {instance.username}")
                
        except Exception as e:
            logger.error(f"Erro ao criar métodos padrão para {instance.username}: {str(e)}")

@receiver(post_migrate)
def create_default_payment_methods_for_existing_users(sender, **kwargs):
    """
    Após migrações, cria métodos padrão para usuários existentes que não os têm.
    Executa apenas em desenvolvimento ou quando explicitamente configurado.
    """
    if settings.DEBUG:
        from django.contrib.auth.models import User
        
        users_without_methods = User.objects.filter(
            payment_methods__isnull=True
        ).exclude(
            username__startswith='test_'  # Exclui usuários de teste
        )
        
        if users_without_methods.exists():
            logger.info(f"Criando métodos padrão para {users_without_methods.count()} usuários existentes...")
            
            for user in users_without_methods:
                try:
                    create_default_payment_methods_for_user(user)
                except Exception as e:
                    logger.error(f"Erro ao criar métodos para {user.username}: {str(e)}")