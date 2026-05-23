from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Goal

@receiver(pre_save, sender=Goal)
def check_goal_completion(sender, instance, **kwargs):
    """Verifica se a meta deve ser automaticamente marcada como concluída"""
    if instance.current >= instance.target:
        instance.completed = True
    elif instance.completed:
        # Se foi manualmente desmarcada mas o valor atual ainda é >= alvo
        if instance.current < instance.target:
            instance.completed = False

@receiver(post_save, sender=Goal)
def goal_saved(sender, instance, created, **kwargs):
    """Log quando uma meta é criada ou atualizada"""
    if created:
        print(f"Nova meta criada: {instance.title} por {instance.user.username}")
    else:
        print(f"Meta atualizada: {instance.title}")