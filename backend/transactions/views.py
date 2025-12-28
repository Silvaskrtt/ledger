from rest_framework import generics
from .models import Transaction, TransactionAccount, TransactionTag, Category, PaymentMethod, Account, Tag
from .serializers import TransactionSerializer, TransactionAccountSerializer, TransactionTagSerializer
from django.views.generic import TemplateView

class CreateTransactionView(TemplateView):
    template_name = "transactions/transaction.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['payment_methods'] = PaymentMethod.objects.all()
        context['transaction_id'] = kwargs.get('pk', None)
        context['accounts'] = Account.objects.all()
        context['tags'] = Tag.objects.all()
        return context

class TransactionListCreateView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransactionAccountListCreateView(generics.ListCreateAPIView):
    queryset = TransactionAccount.objects.all()
    serializer_class = TransactionAccountSerializer


class TransactionAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransactionAccount.objects.all()
    serializer_class = TransactionAccountSerializer


class TransactionTagListCreateView(generics.ListCreateAPIView):
    queryset = TransactionTag.objects.all()
    serializer_class = TransactionTagSerializer


class TransactionTagDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransactionTag.objects.all()
    serializer_class = TransactionTagSerializer
