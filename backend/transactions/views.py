from django.shortcuts import render
from django.views import View
from rest_framework import viewsets

from .forms import TransactionForm
from .models import Transaction, TransactionAccount, TransactionTag
from .serializers import TransactionSerializer, TransactionAccountSerializer, TransactionTagSerializer

class TransactionCreatedView(View):
    template_name = 'transactions/transaction.html' # ainda nao tem frontend
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'form': TransactionForm(),
            # ainda falta implementar mais funcionalidades
            'transactions': Transaction.objects.all()
        })
        
    def post(self, request, *args, **kwargs):
        print("Debug: Recebido POST em TransactionView")
        
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            # redirecionar ou renderizar com sucesso
        return render(request, self.template_name, {
            'form': form,
            'transactions': Transaction.objects.all()
        })
        
        if not form.is_valid():
            print("Debug: Formulário inválido")
            print(form.errors)
            return render(request, self.template_name, {
                'form': form, })

        transaction = form.save()
        
        return render(request, self.template_name, {
            'form': TransactionForm(),
            'transactions': Transaction.objects.all()
        })

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransactionAccountViewSet(viewsets.ModelViewSet):
    queryset = TransactionAccount.objects.all()
    serializer_class = TransactionAccountSerializer


class TransactionTagViewSet(viewsets.ModelViewSet):
    queryset = TransactionTag.objects.all()
    serializer_class = TransactionTagSerializer
