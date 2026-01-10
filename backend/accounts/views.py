# backend/accounts/views.py

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from .models import Account
from .serializers import AccountSerializer, CreditCardSerializer

class AccountListCreateView(generics.ListCreateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


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


def account_management_view(request):
    return render(request, 'account/account_management.html')