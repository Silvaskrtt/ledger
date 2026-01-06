# views.py
from rest_framework import generics, status
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import make_aware
from datetime import datetime
from django.shortcuts import render
from django.db import transaction as db_transaction
import logging
import uuid
from .models import Transaction, TransactionAccount, TransactionTag, Category, PaymentMethod, Account, Tag
from .serializers import TransactionCreateSerializer, TransactionUpdateSerializer, TransactionAccountSerializer, TransactionTagSerializer

logger = logging.getLogger(__name__)

class CreateTransactionView(LoginRequiredMixin, TemplateView):
    template_name = "transactions/transaction.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['categories'] = Category.objects.all()
        context['payment_methods'] = PaymentMethod.objects.all()
        context['accounts'] = Account.objects.filter(user=self.request.user)
        context['tags'] = Tag.objects.filter(id_user=self.request.user)
        
        return context

class TransactionListView(LoginRequiredMixin, TemplateView):
    template_name = "transactions/transaction_history.html"

    def get(self, request, *args, **kwargs):
        transactions = Transaction.objects.filter(
            id_user=request.user
        ).select_related(
            "id_category",
            "id_payment_method"
        ).prefetch_related(
            "transaction_accounts__id_account"
        ).order_by(
            "-occurred_at"
        )

        start = request.GET.get("start")
        end = request.GET.get("end")
        category_uuid = request.GET.get("category")

        if start and end:
            try:
                start_date = make_aware(datetime.strptime(start, "%Y-%m-%d"))
                end_date = make_aware(datetime.strptime(end, "%Y-%m-%d"))
                transactions = transactions.filter(
                    occurred_at__range=(start_date, end_date)
                )
            except ValueError:
                pass

        # FILTRO DE CATEGORIA
        if category_uuid and category_uuid != "":
            try:
                # Converter string para UUID
                category_uuid_obj = uuid.UUID(category_uuid)
                # Filtrar usando o campo correto (id_category_id é o ForeignKey)
                transactions = transactions.filter(id_category_id=category_uuid_obj)
                transactions = transactions.filter(id_category_id=category_uuid_obj)
                print(f"DEBUG - Filtrando por categoria UUID: {category_uuid_obj}")
                print(f"DEBUG - Transações após filtro: {transactions.count()}")
            except (ValueError, AttributeError) as e:
                print(f"DEBUG - Erro no UUID da categoria: {e}")
                # Se não for um UUID válido, tenta filtrar por nome
                transactions = transactions.filter(id_category__name__icontains=category_uuid)

        context = {
            "transactions": transactions,
            "categories": Category.objects.all(),
            "accounts": Account.objects.filter(user=request.user),
            "tags": Tag.objects.filter(id_user=request.user),
            "payment_methods": PaymentMethod.objects.all(),
            "start": start or "",
            "end": end or "",
            "selected_category": category_uuid or "",
        }
        return render(request, self.template_name, context)

class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionCreateSerializer

    def get_queryset(self):
        return Transaction.objects.filter(id_user=self.request.user)

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            
            validated_data = serializer.validated_data.copy()
            category_instance = validated_data.pop('id_category')
            payment_method_instance = validated_data.pop('id_payment_method')
            account_id = validated_data.pop('id_account')
            tags = validated_data.pop('tags', [])
            
            transaction_obj = Transaction.objects.create(
                id_user=request.user,
                id_category=category_instance,
                id_payment_method=payment_method_instance,
                **validated_data
            )
            
            TransactionAccount.objects.create(
                id_transaction=transaction_obj,
                id_account_id=account_id,
                role='source' if transaction_obj.direction == 'OUT' else 'destination'
            )
            
            account = Account.objects.get(id=account_id)

            if transaction_obj.direction == 'OUT':
                account.balance -= transaction_obj.amount
            else:
                account.balance += transaction_obj.amount

            account.save()
            
            for tag_uuid in tags:
                try:
                    TransactionTag.objects.create(
                        id_transaction=transaction_obj,
                        id_tag_id=tag_uuid
                    )
                except Exception as e:
                    logger.warning(f"Erro ao relacionar tag {tag_uuid}: {e}")
            
            return Response({
                'id_transaction': str(transaction_obj.id_transaction),
                'message': 'Transação criada com sucesso'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erro ao criar transação: {str(e)}")
            return Response(
                {'detail': 'Erro ao processar a transação. Tente novamente.'},
                status=status.HTTP_400_BAD_REQUEST
            )

class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionUpdateSerializer
    
    def get_queryset(self):
        return Transaction.objects.filter(id_user=self.request.user)

class TransactionAccountListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionAccountSerializer
    
    def get_queryset(self):
        return TransactionAccount.objects.filter(id_transaction__id_user=self.request.user)

class TransactionAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionAccountSerializer
    
    def get_queryset(self):
        return TransactionAccount.objects.filter(id_transaction__id_user=self.request.user)

class TransactionTagListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionTagSerializer
    
    def get_queryset(self):
        return TransactionTag.objects.filter(id_transaction__id_user=self.request.user)

class TransactionTagDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionTagSerializer
    
    def get_queryset(self):
        return TransactionTag.objects.filter(id_transaction__id_user=self.request.user)