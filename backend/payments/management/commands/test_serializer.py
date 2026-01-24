from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Account
from categories.models import Category
from payments.models import PaymentMethod
from decimal import Decimal
import json

class Command(BaseCommand):
    help = 'Testar serializer de transação'

    def handle(self, *args, **options):
        user = User.objects.get(username='Murilo')
        
        print("=== TESTANDO SERIALIZER ===")
        
        # Dados de teste
        test_data = {
            'amount': '9.00',
            'direction': 'OUT',
            'currency': 'BRL',
            'origin': 'MANUAL',
            'category': 'd7b88a6d-6c9a-4a49-a898-46518212f397',
            'payment_method': 'b82f2a18-59ce-46ca-b64a-4ca37414758d',
            'account': 'a28888c5-fedd-4c61-a61d-718ab7a05f9c',
            'occurred_at': '2026-01-24T05:23',
            'description': 'Teste serializer',
            'tags': []
        }
        
        # Criar contexto de request fake
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        
        factory = APIRequestFactory()
        request = factory.post('/api/transactions/', test_data)
        request.user = user
        
        # Testar serializer
        from transactions.serializers import TransactionCreateSerializer
        
        serializer = TransactionCreateSerializer(
            data=test_data,
            context={'request': request}
        )
        
        print("Validando serializer...")
        if serializer.is_valid():
            print("✓ Serializer válido!")
            
            try:
                print("Salvando...")
                result = serializer.save()
                print(f"✓ Sucesso! Resultado: {result}")
                
            except Exception as e:
                print(f"✗ Erro ao salvar: {str(e)}")
                import traceback
                traceback.print_exc()
                
        else:
            print("✗ Serializer inválido!")
            print("Erros:", json.dumps(serializer.errors, indent=2, ensure_ascii=False))