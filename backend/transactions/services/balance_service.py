# backend/transactions/services/balance_service.py

from django.db.models import Sum
from accounts.models import Account
from transactions.models import Transaction

def recalculate_account_balance(account):
    """
    Recalcula o saldo de uma conta baseado nas transações relacionadas.
    
    Princípio: A transação é a fonte da verdade para o saldo.
    Esta função recalcula o saldo somando todas as transações associadas
    à conta, garantindo consistência entre o modelo Account e Transaction.
    
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
    # Agregação otimizada: agrupa transações por direção e soma valores
    totals = (
        Transaction.objects
        # Filtra transações relacionadas à conta através do relacionamento TransactionAccount
        .filter(transaction_accounts__id_account=account)
        # Agrupa resultados pela direção da transação (IN/OUT)
        .values('direction')
        # Soma os valores para cada grupo de direção
        .annotate(total=Sum('amount'))
    )

    # Inicializa saldo como zero
    balance = 0
    
    # Processa os totais agregados
    for item in totals:
        if item['direction'] == 'IN':
            # Entradas aumentam o saldo
            balance += item['total']
        else:
            # Saídas diminuem o saldo
            balance -= item['total']

    # Atualiza apenas o campo balance da conta (otimização de performance)
    account.balance = balance
    account.save(update_fields=['balance'])

    return balance