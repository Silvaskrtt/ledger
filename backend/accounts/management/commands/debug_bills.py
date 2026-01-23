# backend/accounts/management/commands/debug_bills.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Account, CreditCardBill
from transactions.models import Transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug de faturas de cartão de crédito'

    def add_arguments(self, parser):
        parser.add_argument(
            '--card-id',
            type=str,
            help='ID do cartão para debug',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Nome de usuário',
        )

    def handle(self, *args, **options):
        card_id = options['card_id']
        username = options['username']
        
        if username:
            user = User.objects.get(username=username)
        else:
            # Primeiro usuário
            user = User.objects.first()
        
        self.stdout.write(f"\n=== DEBUG Faturas para usuário: {user.username} ===")
        
        if card_id:
            cards = Account.objects.filter(account=card_id, user=user, type='CREDIT_CARD')
        else:
            cards = Account.objects.filter(user=user, type='CREDIT_CARD')
        
        for card in cards:
            self.stdout.write(f"\n--- Cartão: {card.name} ({card.account}) ---")
            self.stdout.write(f"Limite: R${card.credit_limit}")
            self.stdout.write(f"Saldo: R${card.balance}")
            self.stdout.write(f"Disponível: R${card.available_credit}")
            self.stdout.write(f"Fechamento: dia {card.closing_day}")
            self.stdout.write(f"Vencimento: dia {card.due_day}")
            
            # Compras
            purchases = Transaction.objects.filter(
                transaction_accounts__account=card,
                transaction_type='PURCHASE',
                is_deleted=False
            )
            self.stdout.write(f"\nCompras totais: {purchases.count()}")
            
            # Compras não vinculadas
            unlinked = purchases.filter(credit_card_bill__isnull=True)
            self.stdout.write(f"Compras não vinculadas: {unlinked.count()}")
            
            for purchase in unlinked[:5]:  # Mostrar até 5
                self.stdout.write(f"  - {purchase.occurred_at.date()}: R${purchase.amount} - {purchase.description}")
            
            # Faturas
            bills = CreditCardBill.objects.filter(credit_card=card).order_by('-end_date')
            self.stdout.write(f"\nFaturas: {bills.count()}")
            
            for bill in bills:
                # Transações vinculadas a esta fatura
                bill_purchases = Transaction.objects.filter(
                    credit_card_bill=bill,
                    transaction_type='PURCHASE',
                    is_deleted=False
                )
                
                bill_payments = Transaction.objects.filter(
                    credit_card_bill=bill,
                    transaction_type='CREDIT_CARD_PAYMENT',
                    is_deleted=False
                )
                
                self.stdout.write(f"\n  Fatura {bill.end_date.strftime('%m/%Y')}:")
                self.stdout.write(f"    Total: R${bill.total_amount}")
                self.stdout.write(f"    Pago: R${bill.paid_amount}")
                self.stdout.write(f"    Pendente: R${bill.total_amount - bill.paid_amount}")
                self.stdout.write(f"    Status: {bill.status}")
                self.stdout.write(f"    Compras vinculadas: {bill_purchases.count()}")
                self.stdout.write(f"    Pagamentos vinculados: {bill_payments.count()}")