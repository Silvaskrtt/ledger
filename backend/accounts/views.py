# backend/accounts/views.py

from asyncio.log import logger
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Account, CreditCardBill, CreditCardPayment
from services.credit_card_service import CreditCardService
from django.utils import timezone
from .serializers import AccountSerializer, CreditCardSerializer
from transactions.services.balance_service import verify_account_balance, sync_all_account_balances
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credit_card_bills(request, card_id):
    """Obtém faturas de um cartão de crédito."""
    try:
        bills = CreditCardService.get_card_bills(card_id, request.user)
        
        bills_data = []
        for bill in bills:
            bills_data.append({
                'id': str(bill.id_bill),
                'start_date': bill.start_date.strftime('%d/%m/%Y'),
                'end_date': bill.end_date.strftime('%d/%m/%Y'),
                'due_date': bill.due_date.strftime('%d/%m/%Y'),
                'total_amount': float(bill.total_amount),
                'paid_amount': float(bill.paid_amount),
                'pending_amount': float(bill.total_amount - bill.paid_amount),
                'minimum_payment': float(bill.minimum_payment),
                'status': bill.status,
                'status_display': bill.get_status_display(),
                'days_until_due': (bill.due_date - timezone.now().date()).days,
                'transactions_count': bill.transactions.count()
            })
        
        return Response({
            'success': True,
            'card_id': card_id,
            'bills': bills_data,
            'count': len(bills_data)
        })
        
    except Account.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Cartão não encontrado'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_credit_card_bill(request):
    """Processa pagamento de uma fatura."""
    try:
        data = json.loads(request.body)
        
        bill_id = data.get('bill_id')
        payment_account_id = data.get('payment_account')
        amount = float(data.get('amount', 0))
        notes = data.get('notes', '')
        create_transaction = data.get('create_transaction', True)
        
        if not all([bill_id, payment_account_id, amount]):
            return Response({
                'success': False,
                'error': 'Dados incompletos'
            }, status=400)
        
        result = CreditCardService.pay_bill(
            bill_id=bill_id,
            payment_account_id=payment_account_id,
            amount=amount,
            user=request.user,
            notes=notes,
            create_transaction=create_transaction
        )
        
        return Response({
            'success': True,
            'message': result['message'],
            'payment_id': str(result['payment'].id_payment),
            'transaction_id': str(result['transaction'].transaction) if result['transaction'] else None,
            'bill': {
                'id': str(result['bill'].id_bill),
                'total_amount': float(result['bill'].total_amount),
                'paid_amount': float(result['bill'].paid_amount),
                'status': result['bill'].status
            },
            'patrimony': result['patrimony']
        })
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Erro no pagamento: {str(e)}")
        return Response({
            'success': False,
            'error': 'Erro ao processar pagamento'
        }, status=500)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_accounts(request):
    """Obtém contas que podem ser usadas para pagar faturas."""
    accounts = Account.objects.filter(
        user=request.user,
        type__in=['CHECKING', 'SAVINGS', 'CASH', 'INVESTMENT'],
        is_active=True
    ).exclude(
        type='CREDIT_CARD'  # Não pode pagar fatura com outro cartão
    )
    
    accounts_data = []
    for account in accounts:
        accounts_data.append({
            'id': str(account.account),
            'name': account.name,
            'type': account.type,
            'type_display': account.get_type_display(),
            'balance': float(account.balance),
            'bank_name': account.bank_name,
            'icon': account.icon,
            'color': account.color
        })
    
    return Response({
        'success': True,
        'accounts': accounts_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_balance_consistency(request):
    """Endpoint para verificar consistência de saldos."""
    accounts = Account.objects.filter(user=request.user)
    results = []
    
    for account in accounts:
        is_consistent, calculated_balance, stored_balance = verify_account_balance(account)
        
        results.append({
            'account': str(account.account),
            'name': account.name,
            'type': account.type,
            'is_consistent': is_consistent,
            'stored_balance': float(stored_balance),
            'calculated_balance': float(calculated_balance),
            'difference': float(stored_balance - calculated_balance)
        })
    
    return Response({
        'results': results,
        'total_accounts': len(results),
        'inconsistent_accounts': len([r for r in results if not r['is_consistent']]),
        'message': 'Use POST /api/accounts/sync-balances/ para corrigir inconsistências'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_account_balances(request):
    """Endpoint para sincronizar saldos."""
    results = sync_all_account_balances(request.user)
    
    return Response({
        'results': results,
        'message': 'Saldos sincronizados com sucesso'
    })

class AccountListCreateView(generics.ListCreateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        # Soft delete: marca como inativa
        instance.is_active = False
        instance.save()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


def account_management_view(request):
    return render(request, 'account/account_management.html')


class CreditCardListCreateView(generics.ListCreateAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Retorna apenas cartões de crédito do usuário
        return Account.objects.filter(
            user=self.request.user,
            type='CREDIT_CARD'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Garante que o tipo seja sempre CREDIT_CARD
        serializer.save(
            user=self.request.user,
            type='CREDIT_CARD'
        )


class CreditCardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Account.objects.filter(
            user=self.request.user,
            type='CREDIT_CARD'
        )


def credit_cards_view(request):
    return render(request, 'card_credit/card_credit.html')


@login_required(login_url='/accounts/login/')
def account_management_view(request):
    return render(request, 'account/account_management.html')