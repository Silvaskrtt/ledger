# backend/payments/management/commands/fix_payment_methods.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from payments.models import PaymentMethod
from payments.defaults import DEFAULT_PAYMENT_METHODS
import uuid

class Command(BaseCommand):
    help = 'Corrige métodos de pagamento para usuários existentes'

    def handle(self, *args, **options):
        self.stdout.write("Verificando métodos de pagamento para todos os usuários...")
        
        for user in User.objects.all():
            methods_count = PaymentMethod.objects.filter(id_user=user).count()
            
            if methods_count == 0:
                self.stdout.write(f"Criando métodos para {user.username}...")
                
                try:
                    for method_data in DEFAULT_PAYMENT_METHODS:
                        PaymentMethod.objects.create(
                            id_payment_method=uuid.uuid4(),
                            id_user=user,
                            type=method_data['type'],
                            description=method_data['description'],
                            requires_account=method_data['requires_account'],
                            allows_installments=method_data['allows_installments']
                        )
                    
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {user.username}: Criados"))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ {user.username}: {str(e)}"))
            else:
                self.stdout.write(f"  ✓ {user.username}: Já tem {methods_count} métodos")
        
        self.stdout.write(self.style.SUCCESS("\nConcluído!"))