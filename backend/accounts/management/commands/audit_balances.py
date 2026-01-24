# backend/accounts/management/commands/fix_payment_discrepancy.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Account, CreditCardBill, CreditCardPayment
from transactions.models import Transaction, TransactionAccount
from decimal import Decimal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige discrepância específica de pagamento de fatura'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Nome de usuário',
        )
        parser.add_argument(
            '--amount',
            type=float,
            required=True,
            help='Valor do pagamento a corrigir',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Data do pagamento (YYYY-MM-DD)',
        )

    def handle(self, *args, **options):
        username = options['username']
        amount = Decimal(str(options['amount']))
        date_str = options.get('date')
        
        user = User.objects.get(username=username)
        
        self.stdout.write(f"=== Corrigindo discrepância para {username} ===")
        self.stdout.write(f"Valor: R${amount:.2f}")
        
        # 1. Buscar todas as contas do usuário
        accounts = Account.objects.filter(user=user)
        
        # 2. Verificar cada conta
        for account in accounts:
            # Buscar transações de pagamento de cartão
            payment_transactions = Transaction.objects.filter(
                transaction_accounts__account=account,
                transaction_type='CREDIT_CARD_PAYMENT',
                amount=amount,
                is_deleted=False
            )
            
            if payment_transactions.exists():
                self.stdout.write(f"\nEncontradas {payment_transactions.count()} transações de R${amount:.2f} na conta {account.name}")
                
                for transaction in payment_transactions:
                    # Verificar se data corresponde
                    if date_str:
                        transaction_date = transaction.occurred_at.date()
                        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if transaction_date != target_date:
                            continue
                    
                    self.stdout.write(f"\nTransação encontrada:")
                    self.stdout.write(f"  ID: {transaction.transaction}")
                    self.stdout.write(f"  Data: {transaction.occurred_at}")
                    self.stdout.write(f"  Descrição: {transaction.description}")
                    
                    # Verificar relações com contas
                    related_accounts = transaction.transaction_accounts.all()
                    for ta in related_accounts:
                        self.stdout.write(f"  Conta relacionada: {ta.account.name} (papel: {ta.role})")
                    
                    # Verificar se está vinculada a uma fatura
                    if transaction.credit_card_bill:
                        bill = transaction.credit_card_bill
                        self.stdout.write(f"  Fatura vinculada: {bill.end_date.strftime('%m/%Y')}")
                        self.stdout.write(f"    Total: R${bill.total_amount:.2f}")
                        self.stdout.write(f"    Pago: R${bill.paid_amount:.2f}")
                    
                    # Perguntar se deve corrigir
                    response = input(f"\nCorrigir esta transação? (s/N): ")
                    if response.lower() == 's':
                        self.fix_transaction_discrepancy(transaction, account)
        
        # 3. Verificar pagamentos de faturas sem transação
        credit_card_payments = CreditCardPayment.objects.filter(
            payment_account__user=user,
            amount=amount
        )
        
        if credit_card_payments.exists():
            self.stdout.write(f"\nEncontrados {credit_card_payments.count()} registros de pagamento sem transação")
            
            for payment in credit_card_payments:
                if not payment.transaction:
                    self.stdout.write(f"\nPagamento sem transação:")
                    self.stdout.write(f"  ID: {payment.id_payment}")
                    self.stdout.write(f"  Data: {payment.paid_at}")
                    self.stdout.write(f"  Conta: {payment.payment_account.name}")
                    self.stdout.write(f"  Fatura: {payment.bill.end_date.strftime('%m/%Y')}")
                    
                    response = input(f"\nCriar transação para este pagamento? (s/N): ")
                    if response.lower() == 's':
                        self.create_missing_transaction(payment)
        
        self.stdout.write(f"\n=== Auditoria completa ===")

    def fix_transaction_discrepancy(self, transaction, account):
        """Corrige uma transação com discrepância."""
        from transactions.services.balance_service import recalculate_account_balance
        
        try:
            # Verificar se a transação está corretamente vinculada às contas
            source_accounts = transaction.transaction_accounts.filter(role='source')
            destination_accounts = transaction.transaction_accounts.filter(role='destination')
            
            self.stdout.write(f"  Status atual:")
            self.stdout.write(f"    Contas fonte: {source_accounts.count()}")
            self.stdout.write(f"    Contas destino: {destination_accounts.count()}")
            
            # Recalcular saldos
            self.stdout.write(f"  Recalculando saldos...")
            
            # Recalcular todas as contas relacionadas
            for ta in transaction.transaction_accounts.all():
                old_balance = ta.account.balance
                new_balance = recalculate_account_balance(ta.account)
                self.stdout.write(f"    {ta.account.name}: R${old_balance:.2f} → R${new_balance:.2f}")
            
            self.stdout.write(self.style.SUCCESS("  ✓ Transação corrigida"))
            
        except Exception as e:
            self.stderr.write(f"  ✗ Erro ao corrigir: {str(e)}")

    def create_missing_transaction(self, payment):
        """Cria transação faltante para um pagamento."""
        from categories.models import Category
        from payments.models import PaymentMethod
        from transactions.services.balance_service import recalculate_account_balance
        
        try:
            # Criar categoria se não existir
            category, _ = Category.objects.get_or_create(
                user=payment.bill.credit_card.user,
                name='Pagamento de Faturas',
                defaults={'color': '#EF4444'}
            )
            
            # Criar método de pagamento se não existir
            payment_method, _ = PaymentMethod.objects.get_or_create(
                user=payment.bill.credit_card.user,
                type='BANK_TRANSFER',
                defaults={'description': 'Transferência para pagar fatura'}
            )
            
            # Criar transação
            transaction = Transaction.objects.create(
                user=payment.bill.credit_card.user,
                amount=payment.amount,
                transaction_type='CREDIT_CARD_PAYMENT',
                direction='OUT',
                currency='BRL',
                origin='MANUAL',
                occurred_at=payment.paid_at,
                description=f"Pagamento fatura {payment.bill.credit_card.name} {payment.bill.end_date.strftime('%m/%Y')}",
                category=category,
                payment_method=payment_method,
                credit_card_bill=payment.bill
            )
            
            # Vincular conta de origem
            TransactionAccount.objects.create(
                transaction=transaction,
                account=payment.payment_account,
                role='source'
            )
            
            # Vincular cartão de destino
            TransactionAccount.objects.create(
                transaction=transaction,
                account=payment.bill.credit_card,
                role='destination'
            )
            
            # Atualizar pagamento com referência à transação
            payment.transaction = transaction
            payment.save()
            
            # Recalcular saldos
            recalculate_account_balance(payment.payment_account)
            recalculate_account_balance(payment.bill.credit_card)
            
            self.stdout.write(self.style.SUCCESS(f"  ✓ Transação criada: {transaction.transaction}"))
            
        except Exception as e:
            self.stderr.write(f"  ✗ Erro ao criar transação: {str(e)}")