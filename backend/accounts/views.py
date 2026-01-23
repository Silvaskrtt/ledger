# backend/accounts/views.py

import logging

from asyncio.log import logger
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .serializers import CreditCardBillSerializer
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import generics
from .models import Account, CreditCardBill, CreditCardPayment
from services.credit_card_service import CreditCardService
from django.utils import timezone
from .serializers import AccountSerializer, CreditCardSerializer
from transactions.services.balance_service import verify_account_balance, sync_all_account_balances
import json

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credit_card_bills(request, card_id):
    """
    Obtém todas as faturas de um cartão de crédito.
    """
    try:
        logger.info(f"=== INICIANDO get_credit_card_bills ===")
        logger.info(f"Card ID: {card_id}")
        logger.info(f"User: {request.user.username}")
        
        # Buscar cartão
        card = get_object_or_404(
            Account, 
            account=card_id, 
            user=request.user,
            type='CREDIT_CARD'
        )
        
        logger.info(f"Cartão encontrado: {card.name} (Dia fechamento: {card.closing_day}, Dia vencimento: {card.due_day})")
        
        # 1. Primeiro, verificar se há compras não vinculadas
        from transactions.models import Transaction
        unlinked_purchases = Transaction.objects.filter(
            transaction_accounts__account=card,
            transaction_type='PURCHASE',
            is_deleted=False,
            credit_card_bill__isnull=True
        )
        
        logger.info(f"Compras não vinculadas encontradas: {unlinked_purchases.count()}")
        
        # 2. Gerar faturas se necessário
        if unlinked_purchases.exists():
            logger.info("Gerando faturas para compras não vinculadas...")
            try:
                bills_created = CreditCardService.generate_credit_card_bills(card)
                logger.info(f"Faturas geradas: {len(bills_created)}")
            except Exception as e:
                logger.error(f"Erro ao gerar faturas: {str(e)}", exc_info=True)
                # Continua mesmo com erro
                
        # 3. Buscar todas as faturas
        bills = CreditCardBill.objects.filter(
            credit_card=card
        ).order_by('-end_date')
        
        logger.info(f"Total de faturas encontradas: {bills.count()}")
        
        # 4. Para cada fatura, garantir que está atualizada
        for bill in bills:
            try:
                bill.recalculate_totals()
                logger.debug(f"Fatura {bill.end_date}: R${bill.total_amount} (pago: R${bill.paid_amount})")
            except Exception as e:
                logger.error(f"Erro ao recalcular fatura {bill.id_bill}: {str(e)}")
                # Continua com próxima fatura
        
        # 5. Serializar dados
        serializer = CreditCardBillSerializer(bills, many=True)
        
        response_data = {
            'success': True,
            'card': {
                'id': str(card.account),
                'name': card.name,
                'type': card.type,
                'credit_limit': float(card.credit_limit) if card.credit_limit else 0,
                'available_credit': float(card.available_credit) if card.available_credit else 0,
                'balance': float(card.balance),
                'closing_day': card.closing_day,
                'due_day': card.due_day
            },
            'bills': serializer.data,
            'count': bills.count()
        }
        
        logger.info(f"=== FINALIZANDO get_credit_card_bills ===")
        return Response(response_data)
        
    except Account.DoesNotExist:
        logger.error(f"Cartão não encontrado: {card_id} para usuário {request.user.username}")
        return Response(
            {'error': 'Cartão não encontrado'},
            status=404
        )
    except Exception as e:
        logger.error(f"Erro em get_credit_card_bills: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Erro interno: {str(e)}'},
            status=500
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_credit_card_bill(request):
    """Processa pagamento de uma fatura."""
    try:
        data = request.data
        
        bill_id = data.get('bill_id')
        payment_account_id = data.get('payment_account')
        amount = data.get('amount')
        notes = data.get('notes', '')
        create_transaction = data.get('create_transaction', True)
        
        print(f"=== DEBUG PAY BILL ===")
        print(f"Bill ID: {bill_id}")
        print(f"Payment Account ID: {payment_account_id}")
        print(f"Amount: {amount}")
        print(f"Type of amount: {type(amount)}")
        print(f"User: {request.user}")
        
        if not all([bill_id, payment_account_id, amount]):
            return Response({
                'success': False,
                'error': 'Dados incompletos'
            }, status=400)
        
        # Converter amount para Decimal
        try:
            from decimal import Decimal, InvalidOperation
            amount_decimal = Decimal(str(amount))  # Converter para string primeiro
        except (ValueError, InvalidOperation, TypeError) as e:
            print(f"Erro na conversão do valor: {e}")
            return Response({
                'success': False,
                'error': f'Valor do pagamento inválido: {str(e)}'
            }, status=400)
        
        if amount_decimal <= Decimal('0'):
            return Response({
                'success': False,
                'error': 'Valor do pagamento deve ser maior que zero'
            }, status=400)
        
        result = CreditCardService.pay_bill(
            bill_id=bill_id,
            payment_account_id=payment_account_id,
            amount=amount_decimal,  # Agora é Decimal, não float
            user=request.user,
            notes=notes,
            create_transaction=create_transaction
        )
        
        print(f"Result: {result}")
        
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
        print(f"ValueError: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.error(f"Erro no pagamento: {str(e)}")
        return Response({
            'success': False,
            'error': f'Erro ao processar pagamento: {str(e)}'
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