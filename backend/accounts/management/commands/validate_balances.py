from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Account
from transactions.services.balance_service import verify_account_balance, sync_all_account_balances
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Valida e corrige consistência entre saldos de contas e transações'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nome de usuário específico para validar (opcional)',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corrige automaticamente saldos inconsistentes',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Valida todos os usuários',
        )

    def handle(self, *args, **options):
        username = options['username']
        fix = options['fix']
        all_users = options['all_users']
        
        if username:
            users = User.objects.filter(username=username)
        elif all_users:
            users = User.objects.all()
        else:
            # Usuário atual do sistema ou todos se vazio
            users = User.objects.all()
        
        total_inconsistent = 0
        total_corrected = 0
        
        for user in users:
            self.stdout.write(f"\n=== Validando usuário: {user.username} ===")
            
            accounts = Account.objects.filter(user=user)
            
            for account in accounts:
                is_consistent, calculated_balance, stored_balance = verify_account_balance(account)
                
                if is_consistent:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {account.name}: R${stored_balance:.2f} (consistente)"
                        )
                    )
                else:
                    total_inconsistent += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ {account.name}: "
                            f"Armazenado=R${stored_balance:.2f}, "
                            f"Calculado=R${calculated_balance:.2f}"
                        )
                    )
                    
                    if fix:
                        account.balance = calculated_balance
                        account.save(update_fields=['balance'])
                        total_corrected += 1
                        self.stdout.write(
                            self.style.WARNING(f"    → Corrigido para R${calculated_balance:.2f}")
                        )
        
        self.stdout.write(f"\n=== RESUMO ===")
        self.stdout.write(f"Contas inconsistentes: {total_inconsistent}")
        self.stdout.write(f"Contas corrigidas: {total_corrected}")
        
        if total_inconsistent > 0 and not fix:
            self.stdout.write(
                self.style.WARNING(
                    "\nUse --fix para corrigir automaticamente saldos inconsistentes"
                )
            )