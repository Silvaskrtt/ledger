# backend/transactions/services/balance_service.py

from asyncio.log import logger
from django.db.models import Sum, Q
from django.db import transaction as db_transaction
from django.db.models import Sum
from accounts.models import Account
from transactions.models import Transaction

def recalculate_account_balance(account):
    """
    Recalcula o saldo de uma conta baseado nas transações relacionadas.
    
    Princípio: A transação é a fonte da verdade para o saldo.
    Esta função recalcula o saldo somando todas as transações associadas
    à conta, garantindo consistência entre o modelo Account e Transaction.
    
    IMPORTANTE: Cartões de crédito têm comportamento diferente:
    - Transações OUT aumentam o saldo (negativo)
    - Transações IN diminuem o saldo (pagamento da fatura)
    
    Args:
        account: Instância do modelo Account a ser recalculada
        
    Returns:
        float: Novo saldo calculado da conta
        
    Processo:
        1. Agrega transações por direção (IN/OUT)
        2. Calcula saldo: entradas positivas, saídas negativas
        3. Atualiza campo balance do modelo Account
        4. Retorna novo saldo
    """
    with db_transaction.atomic():
        # Bloqueia a conta para evitar condições de corrida
        locked_account = Account.objects.select_for_update().get(pk=account.pk)
    
    # Calcula saldo baseado em todas as transações não deletadas
    totals = (
        Transaction.objects
        .filter(
            Q(transaction_accounts__id_account=locked_account) &
            Q(is_deleted=False)  # Ignorar transações deletadas
        )
        .values('direction')
        .annotate(total=Sum('amount'))
    )

    # Inicializa saldo como zero
    balance = 0
    
    # Processa os totais agregados
    for item in totals:
            if item['direction'] == 'IN':
                if locked_account.is_credit_card:
                    # Para cartões de crédito, entradas (pagamentos) diminuem o saldo
                    balance -= item['total']
                else:
                    # Para outras contas, entradas aumentam o saldo
                    balance += item['total']
            else:  # OUT
                if locked_account.is_credit_card:
                    # Para cartões de crédito, saídas (compras) aumentam o saldo (negativo)
                    balance += item['total']  # Soma positiva porque saldo é negativo
                else:
                    # Para outras contas, saídas diminuem o saldo
                    balance -= item['total']
        
    # Saldo é negativo para cartões de crédito (representa dívida)
    if locked_account.is_credit_card:
            # O saldo do cartão deve ser negativo ou zero
            # Não pode ser positivo porque não pode ter crédito em cartão
            balance = -abs(balance)
        
    logger.info(f"Recalculando saldo da conta {locked_account.name}: {locked_account.balance} -> {balance}")
        
        # Atualiza apenas se mudou
    if locked_account.balance != balance:
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