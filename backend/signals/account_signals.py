# signals/account_signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from transactions.models import Transaction

@receiver(post_save, sender=Transaction)
def update_account_balance(sender, instance, created, **kwargs):
    """Atualiza saldo da conta automaticamente quando transação é criada."""
    if created and not instance.is_deleted:
        # Para cada conta relacionada à transação
        for transaction_account in instance.transaction_accounts.all():
            account = transaction_account.account
            account.refresh_balance()  # Recalcula saldo