from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
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
from payments.models import InstallmentPlan, PaymentMethod
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
        
        logger.info(f"=== API CREATE TRANSACTION ===")
        logger.info(f"Usuário: {request.user.username}")
        logger.info(f"Dados recebidos: {request.data}")
        
        try:
            # Validação dos dados de entrada
            serializer = self.get_serializer(
                data=request.data, 
                context={'request': request}
            )
            
            logger.info("Validando serializer...")
            serializer.is_valid(raise_exception=True)
            logger.info("Serializer validado com sucesso")
            
            # O serializer já chama o serviço
            logger.info("Chamando serializer.save()...")
            result = serializer.save()
            logger.info(f"Resultado: {result['type']}")
            
            # Formata resposta baseada no tipo
            response_data = {
                'success': True,
                'message': result['message'],
                'type': result['type']
            }
            
            # Adicionar dados específicos
            if result['type'] == 'MANUAL':
                transaction = result['data']
                response_data.update({
                    'transaction_id': str(transaction.transaction),
                    'amount': float(transaction.amount),
                    'direction': transaction.direction,
                    'transaction_type': transaction.transaction_type
                })
            
            logger.info(f"Transação criada com sucesso: {response_data}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # LOG DETALHADO DO ERRO
            logger.error(f"Erro ao criar transação: {str(e)}", exc_info=True)
            
            # Retornar erro detalhado
            return Response({
                'detail': str(e),
                'error_type': type(e).__name__,
                'message': 'Erro ao processar a transação'
            }, status=status.HTTP_400_BAD_REQUEST)


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
    
    # Sobrescreve para usar serializer diferente na atualização
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TransactionUpdateSerializer
        return TransactionCreateSerializer
    
    def get_queryset(self):
        """Garante que usuário só acesse suas próprias transações."""
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # Recalcular saldo da conta após atualização
        for ta in instance.transaction_accounts.all():
            recalculate_account_balance(ta.account)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # 1. CAPTURAR CONTA ANTES DA EXCLUSÃO
            old_accounts = list(instance.transaction_accounts.all())
            old_bill = instance.credit_card_bill
            
            # Verificar se é transação parcelada
            is_installment = instance.installment_plan is not None
            
            # Verificar se tem fatura vinculada
            has_bill = instance.credit_card_bill is not None
            
            # LOG para debug
            logger.info(f"Excluindo transação {instance.transaction}")
            logger.info(f"  Tipo: {instance.transaction_type}")
            logger.info(f"  Parcelada: {is_installment}")
            logger.info(f"  Fatura vinculada: {has_bill}")
            
            # 2. EXECUTAR A EXCLUSÃO (soft delete)
            self.perform_destroy(instance)
            
            # 3. RECALCULAR SALDO DAS CONTAS AFETADAS
            for ta in old_accounts:
                recalculate_account_balance(ta.account)
            
            # 4. ATUALIZAR FATURA SE HOUVER
            if old_bill:
                logger.info(f"  Atualizando fatura {old_bill.end_date}")
                old_bill.recalculate_totals()
            
            # Recalcular saldo das contas afetadas
            affected_accounts = list(instance.transaction_accounts.all())
            for ta in affected_accounts:
                recalculate_account_balance(ta.account)
            
            # ATUALIZAR FATURA SE HOUVER
            if has_bill:
                bill = instance.credit_card_bill
                logger.info(f"  Atualizando fatura {bill.end_date}")
                bill.recalculate_totals()
                
            # Se for transação parcelada, oferecer opção de excluir outras
            if is_installment:
                response_data = {
                    'success': True,
                    'message': 'Transação excluída com sucesso.',
                    'is_installment': True,
                    'installment_plan_id': str(instance.installment_plan.installment_plan),
                    'suggestion': 'Esta transação é parte de um parcelamento. Deseja excluir as outras parcelas também?'
                }
            else:
                response_data = {
                    'success': True,
                    'message': 'Transação excluída com sucesso.'
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Transaction.DoesNotExist:
            return Response(
                {'detail': 'Transação não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erro ao excluir transação: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Erro ao excluir transação: {str(e)}'},
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


class InstallmentPlanDeleteView(generics.GenericAPIView):
    """
    View para excluir parcelamentos completos.
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, plan_id, *args, **kwargs):
        """
        Exclui um plano de parcelamento completo.
        Opções:
        - delete_future: Excluir apenas parcelas futuras (default)
        - delete_all: Excluir todas as parcelas
        """
        try:
            # Buscar plano de parcelamento
            plan = InstallmentPlan.objects.get(
                installment_plan=plan_id,
                user=request.user
            )
            
            # Obter parâmetros
            delete_all = request.query_params.get('delete_all', 'false').lower() == 'true'
            delete_future_only = request.query_params.get('delete_future_only', 'true').lower() == 'true'
            
            # Buscar transações do parcelamento
            if delete_all:
                transactions = Transaction.objects.filter(
                    installment_plan=plan,
                    is_deleted=False
                )
                message = "Todas as parcelas do parcelamento foram excluídas."
            else:
                # Excluir apenas parcelas futuras
                transactions = Transaction.objects.filter(
                    installment_plan=plan,
                    occurred_at__gt=timezone.now(),
                    is_deleted=False
                )
                message = "Parcelas futuras do parcelamento foram excluídas."
            
            # Contar antes da exclusão
            count_before = transactions.count()
            
            # Marcar como deletadas
            for transaction in transactions:
                transaction.is_deleted = True
                transaction.deleted_at = timezone.now()
                transaction.save()
                
                # Recalcular contas afetadas
                for ta in transaction.transaction_accounts.all():
                    recalculate_account_balance(ta.account)
                
                # Recalcular faturas se houver
                if transaction.credit_card_bill:
                    transaction.credit_card_bill.recalculate_totals()
            
            return Response({
                'success': True,
                'message': message,
                'transactions_deleted': count_before,
                'plan_id': str(plan.installment_plan),
                'delete_all': delete_all
            }, status=status.HTTP_200_OK)
            
        except InstallmentPlan.DoesNotExist:
            return Response(
                {'detail': 'Plano de parcelamento não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erro ao excluir parcelamento: {str(e)}")
            return Response(
                {'detail': f'Erro ao excluir parcelamento: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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


# Adicione estas views de teste também
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_simple_transaction(request):
    """Endpoint simplificado para testar transação."""
    from decimal import Decimal
    
    try:
        # Usar dados hardcoded para testar
        account = Account.objects.get(
            account="a28888c5-fedd-4c61-a61d-718ab7a05f9c",
            user=request.user
        )
        
        category = Category.objects.get(
            category="d7b88a6d-6c9a-4a49-a898-46518212f397",
            user=request.user
        )
        
        payment_method = PaymentMethod.objects.get(
            payment_method="b82f2a18-59ce-46ca-b64a-4ca37414758d",
            user=request.user
        )
        
        logger.info(f"=== TEST SIMPLE TRANSACTION ===")
        logger.info(f"User: {request.user.username}")
        logger.info(f"Account: {account.name} ({account.type})")
        logger.info(f"Category: {category.name}")
        logger.info(f"Payment Method: {payment_method.get_type_display()} ({payment_method.type})")
        
        # Criar transação manualmente
        transaction = Transaction.objects.create(
            user=request.user,
            category=category,
            payment_method=payment_method,
            amount=Decimal('7.5'),
            direction='OUT',
            transaction_type='EXPENSE',
            currency='BRL',
            origin='MANUAL',
            description='Moto 99 - Teste Simples'
        )
        
        TransactionAccount.objects.create(
            transaction=transaction,
            account=account,
            role='source'
        )
        
        # Recalcular saldo
        recalculate_account_balance(account)
        
        return Response({
            'success': True,
            'message': 'Transação de teste criada!',
            'transaction_id': str(transaction.transaction),
            'account_balance': float(account.balance)
        })
        
    except Exception as e:
        logger.error(f"Erro no teste simples: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_transaction_api(request):
    """Endpoint para testar API de transação."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=== TEST API ENDPOINT ===")
    logger.info(f"User: {request.user}")
    logger.info(f"Data: {request.data}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Tentar criar transação simples
    from decimal import Decimal
    
    try:
        account = Account.objects.get(
            account="a28888c5-fedd-4c61-a61d-718ab7a05f9c",
            user=request.user
        )
        category = Category.objects.get(
            category="d7b88a6d-6c9a-4a49-a898-46518212f397",
            user=request.user
        )
        payment_method = PaymentMethod.objects.get(
            payment_method="b82f2a18-59ce-46ca-b64a-4ca37414758d",
            user=request.user
        )
        
        transaction = Transaction.objects.create(
            user=request.user,
            category=category,
            payment_method=payment_method,
            amount=Decimal('7.5'),
            direction='OUT',
            transaction_type='EXPENSE',
            currency='BRL',
            origin='MANUAL',
            description='Moto 99 - Teste API'
        )
        
        TransactionAccount.objects.create(
            transaction=transaction,
            account=account,
            role='source'
        )
        
        return Response({
            'success': True,
            'message': 'Transação criada via API',
            'transaction_id': str(transaction.transaction)
        })
        
    except Exception as e:
        logger.error(f"Erro: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simple_debug_view(request):
    """View simples para debug."""
    logger.info("=" * 50)
    logger.info("=== SIMPLE DEBUG VIEW ===")
    logger.info(f"User: {request.user.username}")
    logger.info(f"Data: {request.data}")
    logger.info(f"Method: {request.method}")
    
    try:
        from decimal import Decimal
        
        account = Account.objects.get(
            account="a28888c5-fedd-4c61-a61d-718ab7a05f9c",
            user=request.user
        )
        
        category = Category.objects.get(
            category="d7b88a6d-6c9a-4a49-a898-46518212f397",
            user=request.user
        )
        
        payment_method = PaymentMethod.objects.get(
            payment_method="b82f2a18-59ce-46ca-b64a-4ca37414758d",
            user=request.user
        )
        
        logger.info(f"Objects found: account={account.name}, category={category.name}, payment_method={payment_method.type}")
        
        # Criar transação manual
        transaction = Transaction.objects.create(
            user=request.user,
            category=category,
            payment_method=payment_method,
            amount=Decimal('9.00'),
            direction='OUT',
            transaction_type='EXPENSE',
            currency='BRL',
            origin='MANUAL',
            description='Debug simple'
        )
        
        TransactionAccount.objects.create(
            transaction=transaction,
            account=account,
            role='source'
        )
        
        from transactions.services.balance_service import recalculate_account_balance
        recalculate_account_balance(account)
        
        logger.info(f"Transaction created: {transaction.transaction}")
        
        return Response({
            'success': True,
            'message': 'Transação criada via debug',
            'transaction_id': str(transaction.transaction)
        })
        
    except Exception as e:
        logger.error(f"ERROR in simple_debug_view: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }, status=400)