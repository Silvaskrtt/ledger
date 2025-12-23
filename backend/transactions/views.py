from rest_framework import viewsets
from .models import Transaction, TransactionAccount, TransactionTag
from .serializers import TransactionSerializer, TransactionAccountSerializer, TransactionTagSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransactionAccountViewSet(viewsets.ModelViewSet):
    queryset = TransactionAccount.objects.all()
    serializer_class = TransactionAccountSerializer


class TransactionTagViewSet(viewsets.ModelViewSet):
    queryset = TransactionTag.objects.all()
    serializer_class = TransactionTagSerializer
