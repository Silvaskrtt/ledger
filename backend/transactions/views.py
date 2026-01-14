# backend/transactions/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import make_aware
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render
from django.db import transaction as db_transaction
import logging
import uuid
from django.core.paginator import Paginator

# Model imports
from transactions.services.balance_service import recalculate_account_balance
from recurrence.models import RecurrenceRule
from transactions.models import Transaction, TransactionAccount, TransactionTag
from categories.models import Category
from payments.models import PaymentMethod
from accounts.models import Account
from tags.models import Tag
from .serializers import TransactionCreateSerializer, TransactionUpdateSerializer, TransactionAccountSerializer, TransactionTagSerializer
from .services.transaction_service import create_transaction_service
from recurrence.services.recurrence_service import process_pending_recurrences
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

class TransactionManagerView(LoginRequiredMixin, TemplateView):
    """
    View principal para gerenciamento de transações com paginação.
    """
    template_name = "transactions/transaction_manager.html"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        transactions = Transaction.objects.filter(
            user=request.user
        ).select_related(
            "category",
            "payment_method"
        ).prefetch_related(
            "transaction_accounts__account",
            "tags"
        ).order_by("-occurred_at")

        # Aplicar filtros
        start = request.GET.get("start")
        end = request.GET.get("end")
        category_uuid = request.GET.get("category")
        account_uuid = request.GET.get("account")

        if start and end:
            try:
                start_date = make_aware(datetime.strptime(start, "%Y-%m-%d"))
                end_date = make_aware(datetime.strptime(end, "%Y-%m-%d"))
                transactions = transactions.filter(
                    occurred_at__range=(start_date, end_date)
                )
            except ValueError:
                pass

        if category_uuid:
            try:
                category_uuid_obj = uuid.UUID(category_uuid)
                transactions = transactions.filter(category_id=category_uuid_obj)
            except (ValueError, AttributeError):
                transactions = transactions.filter(category__name__icontains=category_uuid)

        if account_uuid:
            try:
                account_uuid_obj = uuid.UUID(account_uuid)
                transactions = transactions.filter(
                    transaction_accounts__account_id=account_uuid_obj
                ).distinct()
            except (ValueError, AttributeError):
                transactions = transactions.filter(
                    transaction_accounts__account__name__icontains=account_uuid
                ).distinct()

        # Paginação
        paginator = Paginator(transactions, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            "transactions": page_obj,
            "categories": Category.objects.filter(user=request.user),
            "accounts": Account.objects.filter(user=request.user),
            "tags": Tag.objects.filter(user=request.user),
            "payment_methods": PaymentMethod.objects.filter(user=request.user),
            "start": start or "",
            "end": end or "",
            "selected_category": category_uuid or "",
            "selected_account": account_uuid or "",
        }
        return render(request, self.template_name, context)


def get_transaction_form(request, transaction_id=None):
    """
    Retorna HTML do formulário para criar/editar transação via AJAX.
    """
    user = request.user
    
    context = {
        'categories': Category.objects.filter(user=user),
        'payment_methods': PaymentMethod.objects.filter(user=user),
        'accounts': Account.objects.filter(user=user),
        'tags': Tag.objects.filter(user=user),
    }
    
    if transaction_id:
        try:
            transaction = Transaction.objects.get(
                transaction=transaction_id,
                user=user
            )
            context['transaction'] = transaction
            
            # Converter tags para lista de IDs
            tag_ids = list(transaction.tags.values_list('tag', flat=True))
            context['selected_tags'] = tag_ids
            
        except Transaction.DoesNotExist:
            return JsonResponse({'error': 'Transação não encontrada'}, status=404)
    
    return render(request, 'transactions/partials/transaction_form.html', context)


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
                transactions = transactions.filter(category__name__icontains=category_uuid)

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
    permission_classes = [IsAuthenticated]  # ✓ Apenas usuários autenticados
    
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
    serializer_class = TransactionCreateSerializer
    
    def get_queryset(self):
        """Garante que usuário só acesse suas próprias transações."""
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # Recalcular saldo da conta após atualização
        for ta in instance.transaction_accounts.all():
            recalculate_account_balance(ta.account)
    
    def destroy(self, request, *args, **kwargs):
        print("=" * 50)
        print("DEBUG: Iniciando exclusão de transação")
        print(f"URL: {request.path}")
        print(f"Transaction ID: {kwargs.get('pk')}")
        print(f"User: {request.user}")
        print(f"Method: {request.method}")
        print("=" * 50)
        
        try:
            instance = self.get_object()
            print(f"Transação encontrada: {instance.transaction}")
            
            # Log das contas afetadas
            affected_accounts = list(instance.transaction_accounts.all())
            print(f"Contas afetadas: {[ta.account.name for ta in affected_accounts]}")
            
            # Executar a exclusão (soft delete)
            self.perform_destroy(instance)
            print("Transação excluída com sucesso")
            
            # AGORA: Recalcular o saldo de todas as contas afetadas
            from transactions.services.balance_service import recalculate_account_balance
            
            for ta in affected_accounts:
                print(f"Recalculando saldo da conta: {ta.account.name}")
                try:
                    # Atualiza o saldo removendo o valor da transação deletada
                    recalculate_account_balance(ta.account)
                    print(f"Saldo da conta {ta.account.name} atualizado: {ta.account.balance}")
                except Exception as e:
                    print(f"Erro ao recalcular saldo da conta {ta.account.name}: {str(e)}")
                    # Continue com outras contas mesmo se uma falhar
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            print(f"Transação não encontrada")
            return Response(
                {'detail': 'Transação não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Erro ao excluir: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def perform_destroy(self, instance):
        """
        Sobrescreve para garantir que a exclusão seja lógica (soft delete)
        e recalculada corretamente.
        """
        # Marca como deletada
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['is_deleted', 'deleted_at'])
        
        # Nota: O recálculo do saldo será feito no método destroy acima


class TransactionAccountListCreateView(generics.ListCreateAPIView):
    """
    API View para gerenciar relações entre transações e contas.
    
    Lista e cria associações TransactionAccount do usuário atual.
    """
    serializer_class = TransactionAccountSerializer
    
    def get_queryset(self):
        """Filtra relações TransactionAccount por transações do usuário."""
        return TransactionAccount.objects.filter(transaction__user=self.request.user)


class TransactionAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API View para operações CRUD em relações TransactionAccount específicas.
    """
    serializer_class = TransactionAccountSerializer
    
    def get_queryset(self):
        """Filtra relações TransactionAccount por transações do usuário."""
        return TransactionAccount.objects.filter(transaction__user=self.request.user)


class TransactionTagListCreateView(generics.ListCreateAPIView):
    """
    API View para gerenciar relações entre transações e tags.
    
    Lista e cria associações TransactionTag do usuário atual.
    """
    serializer_class = TransactionTagSerializer
    
    def get_queryset(self):
        """Filtra relações TransactionTag por transações do usuário."""
        return TransactionTag.objects.filter(transaction__user=self.request.user)


class TransactionTagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API View para operações CRUD em relações TransactionTag específicas.
    """
    serializer_class = TransactionTagSerializer
    
    def get_queryset(self):
        """Filtra relações TransactionTag por transações do usuário."""
        return TransactionTag.objects.filter(transaction__user=self.request.user)