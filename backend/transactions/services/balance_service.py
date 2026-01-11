# backend/transactions/services/balance_service.py

from asyncio.log import logger
from django.db.models import Sum, Q
from django.db import transaction as db_transaction
from django.db.models import Sum
from accounts.models import Account
from transactions.models import Transaction

def recalculate_account_balance(account):
    """
    Recalcula saldo CORRETAMENTE baseado em transações.
    FÓRMULA ÚNICA E CONSISTENTE.
    """
    with db_transaction.atomic():
        locked_account = Account.objects.select_for_update().get(pk=account.pk)
        
        # 1. Para TODAS as contas: pegar saldo inicial
        balance = locked_account.initial_balance
        
        # 2. Calcular totais de transações
        totals_in = Transaction.objects.filter(
            transaction_accounts__id_account=locked_account,
            direction='IN',
            is_deleted=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        totals_out = Transaction.objects.filter(
            transaction_accounts__id_account=locked_account,
            direction='OUT',
            is_deleted=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # 3. APLICAR FÓRMULA ÚNICA
        if locked_account.is_credit_card:
            # Cartão: saldo = dívida (negativo)
            # OUT aumenta dívida, IN reduz dívida
            balance = totals_out - totals_in  # Negativo = dívida
        else:
            # Conta normal: saldo = dinheiro disponível
            # IN aumenta saldo, OUT reduz saldo
            balance = locked_account.initial_balance + totals_in - totals_out
        
        # 4. Garantir que cartões nunca tenham saldo positivo
        if locked_account.is_credit_card and balance > 0:
            balance = 0  # Cartão não pode ter crédito
        
        # 5. Atualizar e retornar
        locked_account.balance = balance
        locked_account.save(update_fields=['balance'])
        
        return balance

def verify_account_balance(account):
    """
    Verifica se o saldo da conta está consistente com as transações.
    
    Usado para validação e debug.
    
    Returns:
        tuple: (is_consistent, calculated_balance, stored_balance)
    """
    with db_transaction.atomic():
        account.refresh_from_db()
        calculated_balance = recalculate_account_balance(account)
        account.refresh_from_db()
        
        is_consistent = abs(account.balance - calculated_balance) < 0.01  # Tolerância de 1 centavo
        
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