# backend/debug_credit_card.py
from accounts.models import Account
from transactions.services.balance_service import verify_account_balance, recalculate_account_balance
from decimal import Decimal

def debug_credit_card(card_id):
    card = Account.objects.get(account=card_id)
    
    print(f"\n=== DEBUG CARTÃO: {card.name} ===")
    print(f"Tipo: {card.type}")
    print(f"Limite: R$ {card.credit_limit}")
    print(f"Saldo atual: R$ {card.balance}")
    print(f"Crédito disponível: R$ {card.available_credit}")
    
    # Verificar consistência
    is_consistent, calculated, stored = verify_account_balance(card)
    print(f"\nConsistência: {'✓ OK' if is_consistent else '✗ INCONSISTENTE'}")
    print(f"Saldo armazenado: R$ {stored}")
    print(f"Saldo calculado: R$ {calculated}")
    
    if not is_consistent:
        print("\nCorrigindo saldo...")
        new_balance = recalculate_account_balance(card)
        card.refresh_from_db()
        print(f"Novo saldo: R$ {card.balance}")
        print(f"Novo crédito disponível: R$ {card.available_credit}")
    
    # Listar transações recentes
    from transactions.models import Transaction, TransactionAccount
    recent_transactions = Transaction.objects.filter(
        transaction_accounts__account=card
    ).order_by('-occurred_at')[:10]
    
    print(f"\nÚltimas 10 transações:")
    for t in recent_transactions:
        ta = t.transaction_accounts.get(account=card)
        print(f"  {t.occurred_at.date()}: {t.direction} R$ {t.amount} "
              f"(role: {ta.role}, desc: {t.description})")