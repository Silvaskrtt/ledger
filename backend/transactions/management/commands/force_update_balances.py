# backend/transactions/management/commands/force_update_balances.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Account
from transactions.services.balance_service import recalculate_account_balance
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Força a atualização de todos os saldos manualmente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nome de usuário específico (opcional)',
        )
        parser.add_argument(
            '--account',
            type=str,
            help='ID da conta específica (opcional)',
        )

    def handle(self, *args, **options):
        username = options['username']
        account_id = options['account']
        
        if username:
            users = User.objects.filter(username=username)
        else:
            users = User.objects.all()
        
        for user in users:
            self.stdout.write(f"\n=== Atualizando saldos para {user.username} ===")
            
            accounts = Account.objects.filter(user=user)
            
            if account_id:
                accounts = accounts.filter(account=account_id)
            
            for account in accounts:
                try:
                    # Saldo antigo
                    old_balance = account.balance
                    
                    # Forçar recalculo
                    new_balance = recalculate_account_balance(account)
                    
                    # Refresh da conta
                    account.refresh_from_db()
                    
                    self.stdout.write(
                        f"  {account.name}: R${old_balance:.2f} → R${account.balance:.2f}"
                    )
                    
                except Exception as e:
                    self.stderr.write(f"  ✗ Erro na conta {account.name}: {str(e)}")
        
        self.stdout.write(f"\n✅ Todos os saldos foram atualizados!")