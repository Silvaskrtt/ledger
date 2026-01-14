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
    Recalcula saldo CORRETAMENTE baseado em transações.
    
    PADRÃO DE SALDO:
    - Contas Normais: Saldo = Saldo_Inicial + Entradas - Saídas
    - Cartões de Crédito: 
        * Transações com role='source' = SAÍDA (aumenta dívida, -)
        * Transações com role='destination' = ENTRADA (reduz dívida, +)
    """
    with db_transaction.atomic():
        locked_account = Account.objects.select_for_update().get(pk=account.pk)
        
        # 1. Para TODAS as contas: saldo inicial
        initial_balance = locked_account.initial_balance
        
        if locked_account.is_credit_card:
            # ============================================
            # CARTÕES DE CRÉDITO - NOVA LÓGICA
            # ============================================
            
            # Buscar todas as relações TransactionAccount deste cartão
            transaction_accounts = TransactionAccount.objects.filter(
                account=locked_account,
                transaction__is_deleted=False
            ).select_related('transaction')
            
            total_debit = Decimal('0')   # Saídas (role='source') - AUMENTAM dívida
            total_credit = Decimal('0')  # Entradas (role='destination') - REDUZEM dívida
            
            for ta in transaction_accounts:
                if ta.role == 'source':
                    # Transação onde cartão é fonte: SAÍDA (aumenta dívida)
                    total_debit += ta.transaction.amount
                elif ta.role == 'destination':
                    # Transação onde cartão é destino: ENTRADA (reduz dívida)
                    total_credit += ta.transaction.amount
            
            # Fórmula: Saldo = Entradas - Saídas (sempre negativo ou zero)
            # Exemplo: 
            #   Compras: 1000 (debit) + Pagamentos: 200 (credit) = 200 - 1000 = -800
            calculated_balance = total_credit - total_debit
            
            # VALIDAÇÃO: Cartão NUNCA pode ter saldo positivo
            if calculated_balance > 0:
                logger.warning(
                    f"Cartão {locked_account.name} teria saldo positivo ({calculated_balance}). "
                    f"Ajustando para 0. Verifique se há entradas incorretas."
                )
                calculated_balance = 0
                
        else:
            # ============================================
            # CONTAS NORMAIS - MANTÉM LÓGICA ORIGINAL
            # ============================================
            totals_in = Transaction.objects.filter(
                transaction_accounts__account=locked_account,
                direction='IN',
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            totals_out = Transaction.objects.filter(
                transaction_accounts__account=locked_account,
                direction='OUT',
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            calculated_balance = initial_balance + totals_in - totals_out
        
        # 4. Atualizar e retornar
        locked_account.balance = calculated_balance
        locked_account.save(update_fields=['balance'])
        
        logger.debug(
            f"Recalculado saldo {locked_account.name}: "
            f"R$ {calculated_balance:.2f} "
            f"(cartão: {locked_account.is_credit_card})"
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