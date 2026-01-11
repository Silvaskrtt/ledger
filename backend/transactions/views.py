# backend/transactions/views.py

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

# Model imports
from recurrence.models import RecurrenceRule
from transactions.models import Transaction, TransactionAccount, TransactionTag
from categories.models import Category
from payments.models import PaymentMethod
from accounts.models import Account
from tags.models import Tag
from .serializers import TransactionCreateSerializer, TransactionUpdateSerializer, TransactionAccountSerializer, TransactionTagSerializer
from .services.transaction_service import create_transaction_service
from recurrence.services.recurrence_service import process_pending_recurrences

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

class CreateTransactionView(LoginRequiredMixin, TemplateView):
    """
    View para renderizar a página de criação de transações.
    
    Fornece ao template todas as opções necessárias para o usuário:
    - Categorias disponíveis
    - Métodos de pagamento
    - Contas do usuário
    - Tags do usuário
    """
    template_name = "transactions/transaction.html"

    def get_context_data(self, **kwargs):
        """Adiciona ao contexto todos os dados necessários para o formulário de transação."""
        context = super().get_context_data(**kwargs)
        
        # Dados para preencher os selects do formulário
        context['categories'] = Category.objects.filter(user=self.request.user)
        context['payment_methods'] = PaymentMethod.objects.filter(user=self.request.user)
        context['accounts'] = Account.objects.filter(user=self.request.user)
        context['tags'] = Tag.objects.filter(user=self.request.user)
        
        return context


class TransactionListView(LoginRequiredMixin, TemplateView):
    """
    View para listar transações do usuário com filtros por período e categoria.
    
    Suporta filtragem por:
    - Intervalo de datas (start/end)
    - Categoria (por UUID ou nome)
    
    Utiliza select_related e prefetch_related para otimizar queries relacionadas.
    """
    template_name = "transactions/transaction_history.html"

    def get(self, request, *args, **kwargs):
        """Processa requisições GET com filtros opcionais."""
        # Query base com otimizações para relações N+1
        transactions = Transaction.objects.filter(
            user=request.user
        ).select_related(
            "category",
            "payment_method"
        ).prefetch_related(
            "transaction_accounts__account"
        ).order_by(
            "-occurred_at"  # Ordena por data mais recente primeiro
        )

        # Filtros da query string
        start = request.GET.get("start")
        end = request.GET.get("end")
        category_uuid = request.GET.get("category")

        # Filtro por intervalo de datas
        if start and end:
            try:
                start_date = make_aware(datetime.strptime(start, "%Y-%m-%d"))
                end_date = make_aware(datetime.strptime(end, "%Y-%m-%d"))
                transactions = transactions.filter(
                    occurred_at__range=(start_date, end_date)
                )
            except ValueError:
                # Ignora erro de parse, mantém query sem filtro de data
                pass

        # Filtro por categoria (pode ser UUID ou nome)
        if category_uuid and category_uuid != "":
            try:
                # Tenta filtrar por UUID
                category_uuid_obj = uuid.UUID(category_uuid)
                transactions = transactions.filter(category_id=category_uuid_obj)
            except (ValueError, AttributeError):
                # Fallback: filtra por nome contendo a string
                transactions = transactions.filter(id_category__name__icontains=category_uuid)

        # Contexto para renderização do template
        context = {
            "transactions": transactions,
            "categories": Category.objects.filter(user=self.request.user),
            "accounts": Account.objects.filter(user=request.user),
            "tags": Tag.objects.filter(user=request.user),
            "payment_methods": PaymentMethod.objects.filter(user=self.request.user),
            "start": start or "",  # Mantém valores dos filtros no template
            "end": end or "",
            "selected_category": category_uuid or "",
        }
        return render(request, self.template_name, context)


class TransactionListCreateView(generics.ListCreateAPIView):
    """
    API View para listar e criar transações.
    
    Features:
    - Lista apenas transações do usuário autenticado
    - Criação atômica com bloqueio de conta para consistência
    - Cálculo automático do saldo da conta após transação
    - Suporte a múltiplas tags por transação
    """
    serializer_class = TransactionCreateSerializer

    def get_queryset(self):
        """Retorna apenas transações do usuário atual."""
        return Transaction.objects.filter(user=self.request.user)

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Cria uma transação com operação atômica para garantir consistência.
        
        Processo:
        1. Valida dados do serializer
        2. Bloqueia a conta para evitar condições de corrida
        3. Cria transação principal
        4. Cria relação com conta (source/destination baseado no direction)
        5. Recalcula saldo da conta
        6. Associa tags à transação
        """
        try:
            # Validação dos dados de entrada
            serializer = self.get_serializer(
                data=request.data, 
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            
            # O serializer já chama o serviço
            result = serializer.save()
            
            # Formata resposta baseada no tipo
            response_data = {
                'success': True,
                'message': result['message'],
                'type': result['type']
            }
            
            # Adiciona dados específicos
            if result['type'] == 'INSTALLMENT':
                data = result['data']
                response_data.update({
                    'installment_plan_id': str(data['installment_plan'].installment_plan),
                    'installments': data['installment_plan'].installments,
                    'installment_amount': float(data['installment_amount']),
                    'total_with_interest': float(data['total_with_interest']),
                    'transactions_created': len(data['transactions'])
                })
            elif result['type'] == 'RECURRENT':
                rule = result['data']
                response_data.update({
                    'recurrence_rule_id': str(rule.recurrence_rule),
                    'frequency': rule.frequency,
                    'next_execution': rule.next_execution,
                    'max_executions': rule.max_executions
                })
            else:  # MANUAL
                transaction = result['data']
                response_data.update({
                    'transaction_id': str(transaction.transaction),
                    'amount': float(transaction.amount),
                    'direction': transaction.direction
                })
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            # Erros de validação do serviço
            logger.error(f"Erro de validação: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erro ao criar transação: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Erro ao processar a transação. Tente novamente.'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProcessRecurrencesView(generics.GenericAPIView):
    """
    Endpoint para processar recorrências pendentes.
    Usar com cron job.
    """
    permission_classes = []  # Ajuste conforme sua autenticação
    
    def post(self, request):
        try:
            count = process_pending_recurrences()
            return Response({
                'processed_count': count,
                'message': f'{count} transações recorrentes processadas'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erro ao processar recorrências: {str(e)}")
            return Response(
                {'detail': 'Erro ao processar recorrências'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API View para operações CRUD em transações específicas.
    
    Permite:
    - Visualizar detalhes de uma transação
    - Atualizar transação existente
    - Excluir transação
    """
    serializer_class = TransactionUpdateSerializer
    
    def get_queryset(self):
        """Garante que usuário só acesse suas próprias transações."""
        return Transaction.objects.filter(user=self.request.user)


class TransactionAccountListCreateView(generics.ListCreateAPIView):
    """
    API View para gerenciar relações entre transações e contas.
    
    Lista e cria associações TransactionAccount do usuário atual.
    """
    serializer_class = TransactionAccountSerializer
    
    def get_queryset(self):
        """Filtra relações TransactionAccount por transações do usuário."""
        return TransactionAccount.objects.filter(id_transaction__user=self.request.user)


class TransactionAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API View para operações CRUD em relações TransactionAccount específicas.
    """
    serializer_class = TransactionAccountSerializer
    
    def get_queryset(self):
        """Filtra relações TransactionAccount por transações do usuário."""
        return TransactionAccount.objects.filter(id_transaction__user=self.request.user)


class TransactionTagListCreateView(generics.ListCreateAPIView):
    """
    API View para gerenciar relações entre transações e tags.
    
    Lista e cria associações TransactionTag do usuário atual.
    """
    serializer_class = TransactionTagSerializer
    
    def get_queryset(self):
        """Filtra relações TransactionTag por transações do usuário."""
        return TransactionTag.objects.filter(id_transaction__user=self.request.user)


class TransactionTagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API View para operações CRUD em relações TransactionTag específicas.
    """
    serializer_class = TransactionTagSerializer
    
    def get_queryset(self):
        """Filtra relações TransactionTag por transações do usuário."""
        return TransactionTag.objects.filter(id_transaction__user=self.request.user)