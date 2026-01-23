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
    Recalcula saldo de forma simplificada.
    ATUALIZADO: Compatível com transaction_type.
    """
    with db_transaction.atomic():
        locked_account = Account.objects.select_for_update().get(pk=account.pk)
        
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
            
            total_purchases = Decimal('0')   # Compras (PURCHASE)
            total_payments = Decimal('0')    # Pagamentos (CREDIT_CARD_PAYMENT)
            
            for ta in transaction_accounts:
                transaction = ta.transaction
                
                if transaction.transaction_type == 'PURCHASE' and ta.role == 'source':
                    # Compras no cartão: aumentam dívida
                    total_purchases += transaction.amount
                elif transaction.transaction_type == 'CREDIT_CARD_PAYMENT' and ta.role == 'destination':
                    # Pagamentos de fatura: reduzem dívida
                    total_payments += transaction.amount
            
            # Fórmula: Dívida = Compras - Pagamentos
            # Saldo NEGATIVO representa dívida
            calculated_balance = -(total_purchases - total_payments)
            
            # Cartão NUNCA pode ter saldo positivo
            if calculated_balance > 0:
                logger.warning(
                    f"Cartão {locked_account.name} com saldo positivo ({calculated_balance}). "
                    f"Verificar transações."
                )
                calculated_balance = Decimal('0')
                
        else:
            # ============================================
            # CONTAS NORMAIS - MANTÉM LÓGICA SIMPLES
            # ============================================
            
            # ENTRADAS (INCOME)
            income_total = Transaction.objects.filter(
                transaction_accounts__account=locked_account,
                transaction_type='INCOME',
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # DESPESAS (EXPENSE, PURCHASE)
            expense_total = Transaction.objects.filter(
                transaction_accounts__account=locked_account,
                transaction_type__in=['EXPENSE', 'PURCHASE'],
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # TRANSFERÊNCIAS
            transfers_in = Transaction.objects.filter(
                transaction_accounts__account=locked_account,
                transaction_type='TRANSFER',
                transaction_accounts__role='destination',
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            transfers_out = Transaction.objects.filter(
                transaction_accounts__account=locked_account,
                transaction_type='TRANSFER',
                transaction_accounts__role='source',
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Fórmula: Saldo = Inicial + Entradas + Transf. Recebidas - Despesas - Transf. Enviadas
            calculated_balance = (
                initial_balance + 
                income_total + 
                transfers_in - 
                expense_total - 
                transfers_out
            )
        
        # Atualizar e retornar
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