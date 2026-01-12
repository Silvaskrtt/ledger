# backend/budgets/views.py
from django.contrib.auth.decorators import login_required
from rest_framework import generics, status
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Budget, BudgetCategoryLimit
from categories.models import Category
from transactions.models import Transaction
from django.db.models import Sum, Prefetch, Q
from .serializers import BudgetSerializer, BudgetCategoryLimitSerializer
from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from datetime import date, datetime
from django.utils.timezone import now, make_aware
import json

def get_or_create_current_month_budget(user):
    """Obtém ou cria um orçamento para o mês atual"""
    today = date.today()
    period_start = today.replace(day=1)
    
    try:
        budget = Budget.objects.get(
            user=user,
            period_type='MONTHLY',
            period_start=period_start,
            is_deleted=False
        )
    except Budget.DoesNotExist:
        budget = Budget.objects.create(
            user=user,
            period_type='MONTHLY',
            period_start=period_start,
            status='ACTIVE'
        )
    
    return budget

@login_required
def budget_view(request):
    """View principal para página de orçamentos."""
    try:
        today = date.today()
        
        # 1. Obter ou criar orçamento do mês atual
        budget = get_or_create_current_month_budget(request.user)
        
        # 2. Buscar todos os limites de categoria para este orçamento
        limits_qs = BudgetCategoryLimit.objects.filter(
            budget=budget
        ).select_related('category').order_by('category__name')
        
        # 3. Calcular valores gastos para cada categoria
        limits = []
        total_limit = 0
        total_spent = 0
        
        for limit in limits_qs:
            # Calcular total gasto nesta categoria no mês atual
            # Filtrar por occurred_at (DateTimeField)
            spent = Transaction.objects.filter(
                user=request.user,
                category=limit.category,
                occurred_at__year=today.year,  # Usar __year
                occurred_at__month=today.month,  # Usar __month
                direction='OUT',  # Apenas saídas (despesas)
                is_deleted=False  # Apenas transações não deletadas
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Calcular valores
            limit_amount = float(limit.limit_amount)
            spent_amount = float(spent)
            
            # Atualizar totais
            total_limit += limit_amount
            total_spent += spent_amount
            
            # Calcular percentual
            if limit_amount > 0:
                percent = (spent_amount / limit_amount) * 100
            else:
                percent = 0
            
            # Calcular restante
            remaining = limit_amount - spent_amount
            
            limits.append({
                'limit': limit,
                'category': limit.category,
                'limit_amount': limit_amount,
                'spent': spent_amount,
                'remaining': remaining,
                'percent': round(percent, 1)
            })
        
        # 4. Calcular percentual geral
        if total_limit > 0:
            overall_percent = (total_spent / total_limit) * 100
        else:
            overall_percent = 0
            
        # 5. Buscar categorias disponíveis para o formulário
        categories = Category.objects.filter(
            user=request.user,
            type__in=['EXPENSE', 'BOTH']  # Apenas categorias de despesa
        ).order_by('name')
        
        context = {
            'limits': limits,
            'categories': categories,
            'current_month': today.strftime('%B %Y'),
            'current_year': today.year,
            'current_month_num': today.month,
            'total_limit': round(total_limit, 2),
            'total_spent': round(total_spent, 2),
            'total_remaining': round(total_limit - total_spent, 2),
            'overall_percent': round(overall_percent, 1),
            'has_budget': bool(limits),
            'budget_id': budget.budget
        }
        
        return render(request, 'budget/budget.html', context)
        
    except Exception as e:
        print(f"Erro na view budget_view: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'budget/budget.html', {
            'limits': [],
            'categories': [],
            'error': str(e),
            'has_budget': False
        })

class BudgetOverviewAPIView(generics.GenericAPIView):
    """API para obter visão geral dos orçamentos (usado pelo JavaScript)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            today = date.today()
            
            # Buscar orçamento do mês atual
            budget = get_or_create_current_month_budget(request.user)
            limits = BudgetCategoryLimit.objects.filter(
                budget=budget
            ).select_related('category')
            
            data = []
            for limit in limits:
                # Calcular gastos - Usar occurred_at
                spent = Transaction.objects.filter(
                    user=request.user,
                    category=limit.category,
                    occurred_at__year=today.year,
                    occurred_at__month=today.month,
                    direction='OUT',
                    is_deleted=False
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                spent_amount = float(spent)
                limit_amount = float(limit.limit_amount)
                
                if limit_amount > 0:
                    percent = min((spent_amount / limit_amount) * 100, 100)
                else:
                    percent = 0
                
                data.append({
                    'id': limit.id,
                    'category': {
                        'id': limit.category.category,
                        'name': limit.category.name
                    },
                    'limit_amount': limit_amount,
                    'spent': spent_amount,
                    'remaining': limit_amount - spent_amount,
                    'percent': round(percent, 1),
                    'budget_id': str(budget.budget)
                })
            
            return Response({
                'success': True,
                'data': data,
                'budget_id': str(budget.budget),
                'month': today.strftime('%B %Y')
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BudgetListCreateView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Budget.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-period_start')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(
            user=self.request.user,
            is_deleted=False
        )

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.deleted_at = now()
        instance.save()

class BudgetCategoryLimitListCreateView(generics.ListCreateAPIView):
    """API para criar e listar limites de categoria"""
    serializer_class = BudgetCategoryLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtrar por budget se fornecido
        budget_id = self.request.query_params.get('budget', None)
        queryset = BudgetCategoryLimit.objects.filter(
            budget__user=self.request.user
        ).select_related('category', 'budget')
        
        if budget_id:
            queryset = queryset.filter(budget__budget=budget_id)
        
        return queryset

    def get_serializer_context(self):
        return {'request': self.request}

class BudgetCategoryLimitDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetCategoryLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BudgetCategoryLimit.objects.filter(
            budget__user=self.request.user
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_budget_limit(request):
    """Endpoint específico para criar limite de orçamento"""
    try:
        data = request.data
        user = request.user
        
        # Validar dados
        category_id = data.get('category')
        limit_amount = data.get('limit_amount')
        month = data.get('month')
        
        if not category_id:
            return Response({
                'success': False,
                'error': 'Categoria é obrigatória'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not limit_amount or float(limit_amount) <= 0:
            return Response({
                'success': False,
                'error': 'Valor da meta deve ser maior que zero'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obter categoria
        try:
            category = Category.objects.get(
                category=category_id,
                user=user
            )
        except Category.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Categoria não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Determinar o mês do orçamento
        if month:
            # Orçamento para mês específico
            period_start = datetime.strptime(month + '-01', '%Y-%m-%d').date()
        else:
            # Mês atual
            today = date.today()
            period_start = today.replace(day=1)
        
        # Obter ou criar orçamento
        budget, created = Budget.objects.get_or_create(
            user=user,
            period_type='MONTHLY',
            period_start=period_start,
            defaults={'status': 'ACTIVE'}
        )
        
        # Verificar se já existe limite para esta categoria neste orçamento
        existing_limit = BudgetCategoryLimit.objects.filter(
            budget=budget,
            category=category
        ).first()
        
        if existing_limit:
            # Atualizar valor existente
            existing_limit.limit_amount = limit_amount
            existing_limit.save()
            limit = existing_limit
            action = 'atualizada'
        else:
            # Criar novo limite
            limit = BudgetCategoryLimit.objects.create(
                budget=budget,
                category=category,
                limit_amount=limit_amount
            )
            action = 'criada'
        
        return Response({
            'success': True,
            'message': f'Meta {action} com sucesso',
            'data': {
                'id': limit.id,
                'category': category.name,
                'limit_amount': str(limit.limit_amount),
                'budget_id': str(budget.budget)
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Função auxiliar para calcular gastos de uma categoria em um período
def get_category_spent_for_period(user, category, start_date, end_date=None):
    """Calcula o total gasto em uma categoria em um período"""
    filters = {
        'user': user,
        'category': category,
        'direction': 'OUT',
        'is_deleted': False,
        'occurred_at__gte': make_aware(datetime.combine(start_date, datetime.min.time()))
    }
    
    if end_date:
        filters['occurred_at__lte'] = make_aware(datetime.combine(end_date, datetime.max.time()))
    
    spent = Transaction.objects.filter(**filters).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    return float(spent)