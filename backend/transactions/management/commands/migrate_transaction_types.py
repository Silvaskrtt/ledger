# backend/transactions/management/commands/migrate_transaction_types.py

from django.core.management.base import BaseCommand
from transactions.models import Transaction, TransactionAccount
from accounts.models import Account
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migra transaction_types para transações existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Nome de usuário específico (opcional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sem salvar alterações',
        )

    def handle(self, *args, **options):
        user_filter = options['user']
        dry_run = options['dry_run']
        
        self.stdout.write("=== MIGRAÇÃO DE TIPOS DE TRANSAÇÃO ===")
        
        # Consultar transações
        transactions = Transaction.objects.all()
        
        if user_filter:
            transactions = transactions.filter(user__username=user_filter)
        
        updated_count = 0
        error_count = 0
        
        for transaction in transactions:
            try:
                old_type = transaction.transaction_type
                
                # Determinar novo tipo baseado no contexto
                new_type = self.determine_transaction_type(transaction)
                
                if old_type != new_type:
                    if not dry_run:
                        transaction.transaction_type = new_type
                        transaction.save(update_fields=['transaction_type'])
                    
                    self.stdout.write(
                        f"  Transação {transaction.transaction}: "
                        f"{old_type} → {new_type}"
                    )
                    updated_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stderr.write(
                    f"  ERRO na transação {transaction.transaction}: {str(e)}"
                )
        
        # Relatório
        self.stdout.write(f"\n=== RESUMO ===")
        self.stdout.write(f"Transações processadas: {transactions.count()}")
        self.stdout.write(f"Transações atualizadas: {updated_count}")
        self.stdout.write(f"Erros: {error_count}")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("\nMODO SIMULAÇÃO: Nenhuma alteração foi salva")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\nMigração concluída com sucesso!")
            )
    
    def determine_transaction_type(self, transaction):
        """Determina o tipo de transação baseado no contexto."""
        
        # Verificar se é transação de cartão de crédito
        credit_card_accounts = transaction.transaction_accounts.filter(
            account__type='CREDIT_CARD'
        )
        
        if credit_card_accounts.exists():
            # É transação em cartão de crédito
            if transaction.direction == 'OUT':
                return 'PURCHASE'
            elif transaction.direction == 'IN':
                return 'CREDIT_CARD_PAYMENT'
        
        # Transação normal
        if transaction.direction == 'IN':
            return 'INCOME'
        elif transaction.direction == 'OUT':
            # Verificar se é transferência (tem mais de uma conta)
            if transaction.transaction_accounts.count() > 1:
                return 'TRANSFER'
            else:
                return 'EXPENSE'
        
        return 'EXPENSE'  # Default