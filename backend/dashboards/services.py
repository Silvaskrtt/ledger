# backend/dashboards/services.py

from django.db.models import Sum, Count, Q, Case, When, F, DecimalField
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from transactions.models import Transaction


class CardExpenseService:
    """Serviço para cálculo de gastos por cartão de crédito"""
    
    @staticmethod
    def get_expenses_by_card(user: User, start_date=None, end_date=None):
        """
        Retorna gastos agrupados por cartão de crédito
        
        Args:
            user: Usuário autenticado
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
        
        Returns:
            List[Dict] com card_name, total_spent e transaction_count
        """
        queryset = Transaction.objects.filter(
            user=user,
            direction='OUT',
            is_deleted=False
        )
        
        # Filtrar por data se fornecido
        if start_date and end_date:
            queryset = queryset.filter(
                occurred_at__range=(start_date, end_date)
            )
        
        # Agrupar por método de pagamento (cartão)
        expenses = queryset.select_related('payment_method').values(
            'payment_method__description',
            'payment_method__type'
        ).annotate(
            total_spent=Sum('amount'),
            transaction_count=Count('transaction')
        ).order_by('-total_spent')
        
        result = []
        total_spent = Decimal('0.00')
        
        for expense in expenses:
            card_name = expense['payment_method__description'] or expense['payment_method__type']
            total = expense['total_spent'] or Decimal('0.00')
            
            result.append({
                'card_name': card_name,
                'card_type': expense['payment_method__type'],
                'total_spent': total,
                'transaction_count': expense['transaction_count']
            })
            total_spent += total
        
        return result, total_spent


class CategoryExpenseService:
    """Serviço para cálculo de gastos por categoria"""
    
    @staticmethod
    def get_expenses_by_category(user: User, include_pending=False, start_date=None, end_date=None):
        """
        Retorna gastos agrupados por categoria com percentual
        
        Args:
            user: Usuário autenticado
            include_pending: Se deve incluir transações pendentes
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
        
        Returns:
            List[Dict] com category_name, total_spent, percentage, transaction_count
        """
        # Base de transações de saída
        queryset = Transaction.objects.filter(
            user=user,
            direction='OUT',
            is_deleted=False
        )
        
        # Filtrar por data se fornecido
        if start_date and end_date:
            queryset = queryset.filter(
                occurred_at__range=(start_date, end_date)
            )
        
        # Calcular total geral
        total_spent = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        if total_spent == 0:
            return [], Decimal('0.00')
        
        # Agrupar por categoria
        expenses = queryset.select_related('category').values(
            'category__category',
            'category__name',
            'category__color'
        ).annotate(
            total_spent=Sum('amount'),
            transaction_count=Count('transaction')
        ).order_by('-total_spent')
        
        result = []
        
        for expense in expenses:
            total = expense['total_spent'] or Decimal('0.00')
            percentage = (total / total_spent * 100) if total_spent > 0 else Decimal('0.00')
            
            result.append({
                'category_id': str(expense['category__category']),
                'category_name': expense['category__name'],
                'category_color': expense['category__color'],
                'total_spent': total,
                'percentage': round(percentage, 2),
                'transaction_count': expense['transaction_count']
            })
        
        return result, total_spent


class CashFlowService:
    """Serviço para cálculo do fluxo de caixa mensal"""
    
    @staticmethod
    def get_monthly_cash_flow(user: User, year: int = None):
        """
        Retorna fluxo de caixa mensal (receitas vs despesas)
        
        Args:
            user: Usuário autenticado
            year: Ano para filtrar (se None, usa ano atual)
        
        Returns:
            List[Dict] com month, income, expense, balance
        """
        if not year:
            year = timezone.now().year
        
        # Definir período do ano
        start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        # Transações do período
        transactions = Transaction.objects.filter(
            user=user,
            is_deleted=False,
            occurred_at__range=(start_date, end_date)
        )
        
        # Dados agrupados por mês
        monthly_data = {}
        
        for month in range(1, 13):
            monthly_data[month] = {
                'income': Decimal('0.00'),
                'expense': Decimal('0.00'),
            }
        
        # Processar cada transação
        for trans in transactions:
            month = trans.occurred_at.month
            amount = trans.amount
            
            if trans.direction == 'IN':
                monthly_data[month]['income'] += amount
            else:
                monthly_data[month]['expense'] += amount
        
        # Construir resultado
        result = []
        month_names = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        
        for month in range(1, 13):
            month_data = monthly_data[month]
            income = month_data['income']
            expense = month_data['expense']
            balance = income - expense
            
            result.append({
                'month': month_names[month - 1],
                'month_number': month,
                'income': income,
                'expense': expense,
                'balance': balance
            })
        
        return result
