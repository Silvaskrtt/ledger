from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Account
from categories.models import Category
from payments.models import PaymentMethod
from decimal import Decimal

class Command(BaseCommand):
    help = 'Debug de criação de transações'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='Murilo')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Usuário 'Murilo' não encontrado!"))
            self.stdout.write("Usuários disponíveis:")
            for u in User.objects.all():
                self.stdout.write(f"  - {u.username}")
            return
        
        print("=== DEBUG DE TRANSAÇÕES ===")
        
        # 1. Verificar conta
        account_id = "a28888c5-fedd-4c61-a61d-718ab7a05f9c"
        try:
            account = Account.objects.get(account=account_id, user=user)
            print(f"✓ Conta encontrada: {account.name} ({account.type})")
            print(f"  Saldo atual: {account.balance}")
            print(f"  É cartão de crédito: {account.is_credit_card}")
        except Account.DoesNotExist:
            print(f"✗ Conta {account_id} não encontrada")
            print("Contas disponíveis:")
            for acc in Account.objects.filter(user=user):
                print(f"  - {acc.name}: {acc.account}")
            return
        
        # 2. Verificar categoria - CORREÇÃO AQUI
        category_id = "d7b88a6d-6c9a-4a49-a898-46518212f397"
        try:
            # O campo é 'category' (UUIDField), não 'id_category'
            category = Category.objects.get(category=category_id, user=user)
            print(f"✓ Categoria encontrada: {category.name}")
        except Category.DoesNotExist:
            print(f"✗ Categoria {category_id} não encontrada")
            print("Categorias disponíveis:")
            for cat in Category.objects.filter(user=user):
                print(f"  - {cat.name}: {cat.category}")
            return
        
        # 3. Verificar método de pagamento - CORREÇÃO AQUI
        payment_method_id = "b82f2a18-59ce-46ca-b64a-4ca37414758d"
        try:
            # O campo é 'payment_method' (UUIDField), não 'id_payment_method'
            payment_method = PaymentMethod.objects.get(
                payment_method=payment_method_id, 
                user=user
            )
            print(f"✓ Método de pagamento encontrado: {payment_method.get_type_display()}")
            print(f"  Tipo: {payment_method.type}")
            print(f"  Descrição: {payment_method.description}")
        except PaymentMethod.DoesNotExist:
            print(f"✗ Método de pagamento {payment_method_id} não encontrada")
            print("Métodos disponíveis:")
            for pm in PaymentMethod.objects.filter(user=user):
                print(f"  - {pm.description} ({pm.type}): {pm.payment_method}")
            return
        
        # 4. Validar compatibilidade
        print("\n4. VALIDANDO COMPATIBILIDADE:")
        try:
            from transactions.services.transaction_service import validate_payment_method_compatibility
            
            is_compatible = validate_payment_method_compatibility(
                payment_method.type,
                account.type
            )
            print(f"✓ Compatibilidade: {is_compatible}")
            
            if not is_compatible:
                print(f"  ERRO: Método {payment_method.type} não compatível com conta {account.type}")
                print("  Regras:")
                print("    - DEBIT: CHECKING, SAVINGS, INVESTMENT, OTHER")
                print("    - CREDIT: apenas CREDIT_CARD")
                print("    - PIX/CASH: CHECKING, SAVINGS, INVESTMENT, CASH, OTHER")
        except Exception as e:
            print(f"✗ Erro ao validar compatibilidade: {str(e)}")
        
        # 5. Testar criação manual
        print("\n=== TESTANDO CRIAÇÃO MANUAL ===")
        try:
            from transactions.services.transaction_service import create_transaction_service
            
            print("  Tentando criar transação...")
            result = create_transaction_service(
                user=user,
                amount=Decimal('7.5'),
                direction='OUT',
                category=category,
                payment_method=payment_method,
                account=account,
                origin='MANUAL',
                description='Moto 99 - Teste'
            )
            
            print(f"✓ Transação criada com sucesso!")
            print(f"  Tipo: {result['type']}")
            if result['type'] == 'MANUAL':
                print(f"  ID: {result['data'].transaction}")
                print(f"  Transaction Type: {result.get('transaction_type', 'N/A')}")
            
        except Exception as e:
            print(f"✗ Erro ao criar transação: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n=== DEBUG COMPLETO ===")