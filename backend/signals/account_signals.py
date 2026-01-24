# backend/signals/account_signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from transactions.models import Transaction, TransactionAccount
from transactions.services.balance_service import recalculate_account_balance
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Transaction)
def update_account_balance_on_transaction_save(sender, instance, created, **kwargs):
    """
    Atualiza saldo da conta automaticamente quando transação é criada ou atualizada.
    CORREÇÃO: Garante que o saldo seja atualizado imediatamente.
    """
    try:
        # Evitar chamada recursiva
        if hasattr(instance, '_updating_balance'):
            return
        
        instance._updating_balance = True
        
        logger.debug(f"=== SIGNAL: Atualizando saldos para transação {instance.transaction} ===")
        
        # Para cada conta relacionada à transação
        for transaction_account in instance.transaction_accounts.all():
            account = transaction_account.account
            
            logger.debug(f"  Conta: {account.name} (role: {transaction_account.role})")
            
            # Recalcular saldo da conta
            old_balance = account.balance
            new_balance = recalculate_account_balance(account)
            
            logger.debug(f"    Saldo: R${old_balance:.2f} → R${new_balance:.2f}")
            
        # Log completo
        logger.info(f"Saldo atualizado para transação {instance.transaction} ({instance.transaction_type})")
        
        # Limpar flag
        del instance._updating_balance
        
    except Exception as e:
        logger.error(f"Erro ao atualizar saldo no signal: {str(e)}", exc_info=True)
        if hasattr(instance, '_updating_balance'):
            del instance._updating_balance

@receiver(pre_delete, sender=Transaction)
def update_account_balance_on_transaction_delete(sender, instance, **kwargs):
    """
    Atualiza saldo da conta antes de uma transação ser deletada (soft delete).
    """
    try:
        logger.debug(f"=== SIGNAL: Atualizando saldos antes de excluir transação {instance.transaction} ===")
        
        # Recalcular saldo de todas as contas relacionadas
        for transaction_account in instance.transaction_accounts.all():
            account = transaction_account.account
            recalculate_account_balance(account)
            
        logger.info(f"Saldos atualizados antes de excluir transação {instance.transaction}")
        
    except Exception as e:
        logger.error(f"Erro ao atualizar saldo antes da exclusão: {str(e)}")

# Também atualizar quando TransactionAccount é criado/atualizado
@receiver(post_save, sender=TransactionAccount)
def update_account_balance_on_transaction_account_save(sender, instance, created, **kwargs):
    """
    Atualiza saldo quando uma relação TransactionAccount é criada ou alterada.
    """
    try:
        if created:
            logger.debug(f"=== SIGNAL: Nova relação TransactionAccount ===")
            logger.debug(f"  Conta: {instance.account.name}")
            logger.debug(f"  Transação: {instance.transaction.transaction}")
            logger.debug(f"  Role: {instance.role}")
            
            # Recalcular saldo da conta
            recalculate_account_balance(instance.account)
    except Exception as e:
        logger.error(f"Erro ao atualizar saldo via TransactionAccount: {str(e)}")