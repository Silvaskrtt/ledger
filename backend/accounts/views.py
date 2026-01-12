# backend/accounts/views.py

from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Account
from .serializers import AccountSerializer, CreditCardSerializer
from transactions.services.balance_service import verify_account_balance, sync_all_account_balances

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