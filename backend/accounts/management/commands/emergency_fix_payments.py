# backend/accounts/management/commands/emergency_fix_payments.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Account, CreditCardBill, CreditCardPayment
from transactions.models import Transaction, TransactionAccount
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Correção emergencial de inconsistências em pagamentos'

    def handle(self, *args, **options):
        self.stdout.write("=== CORREÇÃO EMERGENCIAL DE PAGAMENTOS ===")
        
        # 1. Corrigir saldos de cartões
        credit_cards = Account.objects.filter(type='CREDIT_CARD')
        for card in credit_cards:
            # Recalcular saldo
            from transactions.services.balance_service import recalculate_account_balance
            old_balance = card.balance
            new_balance = recalculate_account_balance(card)
            
            if old_balance != new_balance:
                self.stdout.write(f"  Cartão {card.name}: {old_balance} → {new_balance}")
        
        # 2. Verificar pagamentos sem transação
        payments = CreditCardPayment.objects.filter(transaction__isnull=True)
        for payment in payments:
            self.stdout.write(f"  Pagamento sem transação: {payment.id_payment} - R${payment.amount}")
            
            # Criar transação faltante
            try:
                from categories.models import Category
                from payments.models import PaymentMethod
                
                # Criar transação
                category, _ = Category.objects.get_or_create(
                    user=payment.bill.credit_card.user,
                    name='Pagamento de Faturas',
                    defaults={'color': '#EF4444'}
                )
                
                payment_method, _ = PaymentMethod.objects.get_or_create(
                    user=payment.bill.credit_card.user,
                    type='BANK_TRANSFER',
                    defaults={'description': 'Transferência para pagar fatura'}
                )
                
                transaction = Transaction.objects.create(
                    user=payment.bill.credit_card.user,
                    amount=payment.amount,
                    transaction_type='CREDIT_CARD_PAYMENT',
                    direction='OUT',
                    currency='BRL',
                    origin='MANUAL',
                    occurred_at=payment.paid_at,
                    description=f"Pagamento fatura {payment.bill.credit_card.name}",
                    category=category,
                    payment_method=payment_method,
                    credit_card_bill=payment.bill
                )
                
                # Vincular contas
                TransactionAccount.objects.create(
                    transaction=transaction,
                    account=payment.payment_account,
                    role='source'
                )
                
                TransactionAccount.objects.create(
                    transaction=transaction,
                    account=payment.bill.credit_card,
                    role='destination'
                )
                
                # Atualizar pagamento
                payment.transaction = transaction
                payment.save()
                
                self.stdout.write(f"    ✓ Transação criada: {transaction.transaction}")
                
            except Exception as e:
                self.stdout.write(f"    ✗ Erro: {str(e)}")
        
        # 3. Verificar transações duplicadas
        transactions = Transaction.objects.filter(
            transaction_type='CREDIT_CARD_PAYMENT'
        ).order_by('occurred_at')
        
        # Agrupar por data, valor e contas
        seen = {}
        duplicates = []
        
        for transaction in transactions:
            key = (
                transaction.occurred_at.date(),
                transaction.amount,
                tuple(sorted([ta.account.account for ta in transaction.transaction_accounts.all()]))
            )
            
            if key in seen:
                duplicates.append(transaction)
            else:
                seen[key] = transaction
        
        if duplicates:
            self.stdout.write(f"  Transações duplicadas: {len(duplicates)}")
            for dup in duplicates:
                self.stdout.write(f"    - {dup.transaction}: R${dup.amount} em {dup.occurred_at}")
                # Marcar como deletada
                dup.is_deleted = True
                dup.save()
        
        self.stdout.write(self.style.SUCCESS("✓ Correção concluída"))