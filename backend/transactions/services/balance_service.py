# backend/transactions/services/balance_service.py

import logging
from django.db.models import Sum, Q
from django.db import transaction as db_transaction
from accounts.models import Account
from transactions.models import Transaction
from transactions.models import TransactionAccount
from decimal import Decimal

logger = logging.getLogger(__name__)

def recalculate_account_balance(account):
    """
    Recalcula saldo de forma consistente.
    ATUALIZADO: Lógica unificada para cartões e contas normais.
    """
    with db_transaction.atomic():
        locked_account = Account.objects.select_for_update().get(pk=account.pk)
        
        initial_balance = locked_account.initial_balance
        
        # Buscar TODAS as relações TransactionAccount
        transaction_accounts = TransactionAccount.objects.filter(
            account=locked_account,
            transaction__is_deleted=False
        ).select_related('transaction')
        
        total_credit = Decimal('0')    # Entradas (IN)
        total_debit = Decimal('0')     # Saídas (OUT)
        
        for ta in transaction_accounts:
            transaction = ta.transaction
            
            if ta.role == 'destination':
                # Dinheiro entrando na conta
                total_credit += transaction.amount
            elif ta.role == 'source':
                # Dinheiro saindo da conta
                total_debit += transaction.amount
        
        # ============================================
        # FÓRMULA UNIFICADA:
        # Saldo = Saldo Inicial + Entradas - Saídas
        # ============================================
        calculated_balance = initial_balance + total_credit - total_debit
        
        # ============================================
        # VALIDAÇÃO ESPECÍFICA PARA CARTÕES
        # ============================================
        if locked_account.is_credit_card:
            # Cartão NUNCA pode ter saldo positivo
            # Balance deve ser <= 0 (zero ou negativo)
            if calculated_balance > 0:
                logger.warning(
                    f"Cartão {locked_account.name} com saldo positivo ({calculated_balance}). "
                    f"Ajustando para 0."
                )
                calculated_balance = Decimal('0')
            
            # Balance NEGATIVO = Dívida
            # Balance ZERO = Sem dívida
            # Balance POSITIVO = IMPOSSÍVEL (corrigido acima)
        
        # ============================================
        # ATUALIZAR E RETORNAR
        # ============================================
        locked_account.balance = calculated_balance
        locked_account.save(update_fields=['balance'])
        
        logger.debug(
            f"Recalculado {locked_account.name} ({locked_account.type}): "
            f"R${calculated_balance:.2f} (cartão: {locked_account.is_credit_card})"
        )
        
        return calculated_balance

def verify_account_balance(account):
    """
    Verifica se o saldo da conta está consistente com as transações.
    """
    with db_transaction.atomic():
        account.refresh_from_db()
        calculated_balance = recalculate_account_balance(account)
        account.refresh_from_db()
        
        is_consistent = abs(account.balance - calculated_balance) < 0.01
        
        if not is_consistent:
            logger.warning(
                f"INCONSISTÊNCIA na conta {account.name}: "
                f"Armazenado={account.balance}, Calculado={calculated_balance}"
            )
        
        return is_consistent, calculated_balance, account.balance

def sync_all_account_balances(user):
    """
    Sincroniza saldos de todas as contas de um usuário.
    
    Útil após migrações ou correções de dados.
    """
    accounts = Account.objects.filter(user=user)
    results = []
    
    for account in accounts:
        try:
            old_balance = account.balance
            new_balance = recalculate_account_balance(account)
            account.refresh_from_db()
            
            if old_balance != new_balance:
                results.append({
                    'account': account.name,
                    'old': old_balance,
                    'new': new_balance,
                    'corrected': True
                })
                logger.info(f"Saldo corrigido: {account.name} {old_balance} -> {new_balance}")
            else:
                results.append({
                    'account': account.name,
                    'balance': new_balance,
                    'corrected': False
                })
                
        except Exception as e:
            logger.error(f"Erro ao sincronizar conta {account.name}: {str(e)}")
            results.append({
                'account': account.name,
                'error': str(e)
            })
    
    return results