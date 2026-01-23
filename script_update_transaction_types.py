# script_update_transaction_types.py
from backend.transactions.models import Transaction
from decimal import Decimal

def update_existing_transactions():
    print("Atualizando tipos de transação existentes...")
    
    # 1. Compras em cartão de crédito
    cc_purchases = Transaction.objects.filter(
        transaction_accounts__account__type='CREDIT_CARD',
        direction='OUT'
    ).exclude(
        description__icontains='pagamento'
    )
    count_cc = cc_purchases.update(transaction_type='PURCHASE')
    print(f"  Compras em cartão: {count_cc}")
    
    # 2. Pagamentos de cartão (baseado na descrição)
    cc_payments = Transaction.objects.filter(
        transaction_accounts__account__type='CREDIT_CARD',
        direction='OUT',
        description__icontains='pagamento'
    )
    count_payments = cc_payments.update(transaction_type='CREDIT_CARD_PAYMENT')
    print(f"  Pagamentos de cartão: {count_payments}")
    
    # 3. Compras normais (outras contas)
    normal_purchases = Transaction.objects.filter(
        direction='OUT'
    ).exclude(
        transaction_accounts__account__type='CREDIT_CARD'
    ).exclude(
        description__icontains='transferência'
    )
    count_normal = normal_purchases.update(transaction_type='PURCHASE')
    print(f"  Compras normais: {count_normal}")
    
    # 4. Receitas
    incomes = Transaction.objects.filter(direction='IN')
    count_incomes = incomes.update(transaction_type='INCOME')
    print(f"  Receitas: {count_incomes}")
    
    # 5. Verificar se alguma ficou sem tipo
    without_type = Transaction.objects.filter(transaction_type='EXPENSE').count()
    print(f"  Transações ainda com tipo EXPENSE (padrão): {without_type}")
    
    print(f"\n✅ Total atualizado: {count_cc + count_payments + count_normal + count_incomes}")

if __name__ == "__main__":
    update_existing_transactions()