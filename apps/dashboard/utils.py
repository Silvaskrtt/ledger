from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from transactions.models import Transaction
from categories.models import Category


class DashboardCalculator:
    """Classe responsável por calcular métricas do dashboard"""
    
    def __init__(self, user):
        self.user = user
        self.today = timezone.now().date()
        
    def get_total_balance(self):
        """Calcula o saldo total do usuário (receitas - despesas)"""
        income = self._get_total_income()
        expenses = self._get_total_expenses()
        return income - expenses
    
    def get_month_balance(self):
        """Calcula o saldo do mês atual"""
        start_date = self.today.replace(day=1)
        end_date = self.today
        
        income = self._get_income_range(start_date, end_date)
        expenses = self._get_expenses_range(start_date, end_date)
        return income - expenses
    
    def get_total_income(self):
        """Retorna total de receitas de todos os tempos"""
        return self._get_total_income()
    
    def get_total_expenses(self):
        """Retorna total de despesas de todos os tempos"""
        return self._get_total_expenses()
    
    def get_current_month_income(self):
        """Retorna receitas do mês atual"""
        start_date = self.today.replace(day=1)
        return self._get_income_range(start_date, self.today)
    
    def get_current_month_expenses(self):
        """Retorna despesas do mês atual"""
        start_date = self.today.replace(day=1)
        return self._get_expenses_range(start_date, self.today)
    
    def get_savings(self):
        """Calcula a economia (diferença entre receitas e despesas do mês)"""
        income = self.get_current_month_income()
        expenses = self.get_current_month_expenses()
        return income - expenses
    
    def get_monthly_trend(self, months=12):
        """Retorna a tendência mensal de receitas e despesas"""
        data = []
        for i in range(months, 0, -1):
            month_date = self.today - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            
            # Get next month's first day
            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
            
            income = self._get_income_range(month_start, month_end)
            expenses = self._get_expenses_range(month_start, month_end)
            
            data.append({
                'month': month_date.strftime('%b/%y'),
                'income': float(income),
                'expenses': float(expenses),
                'balance': float(income - expenses)
            })
        
        return data
    
    def get_expenses_by_category(self, period='month'):
        """Retorna despesas agrupadas por categoria"""
        start_date = self._get_period_start_date(period)
        
        categories = Category.objects.filter(
            user=self.user,
            type='expense'
        )
        
        data = []
        for category in categories:
            amount = Transaction.objects.filter(
                user=self.user,
                category=category,
                type='expense',
                date__gte=start_date,
                date__lte=self.today
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            if amount > 0:  # Only include categories with expenses
                data.append({
                    'name': category.name,
                    'amount': float(amount),
                    'icon': category.icon,
                    'percentage': 0  # Will be calculated on frontend
                })
        
        # Calculate percentages
        total = sum(item['amount'] for item in data)
        if total > 0:
            for item in data:
                item['percentage'] = round((item['amount'] / total) * 100, 1)
        
        return sorted(data, key=lambda x: x['amount'], reverse=True)
    
    def get_recent_transactions(self, limit=5):
        """Retorna as transações recentes do usuário"""
        transactions = Transaction.objects.filter(
            user=self.user
        ).select_related('category')[:limit]
        
        data = []
        for transaction in transactions:
            data.append({
                'id': transaction.id,
                'title': transaction.description,
                'category': transaction.category.name,
                'amount': float(transaction.amount),
                'type': transaction.type,
                'date': transaction.date.strftime('%d/%m/%Y'),
                'icon': transaction.category.icon,
            })
        
        return data
    
    def get_budget_by_category(self):
        """Retorna orçamento/gasto por categoria"""
        expenses = self.get_expenses_by_category('month')
        return expenses
    
    def get_income_percentage_change(self, months=1):
        """Calcula a variação percentual de receitas comparado ao período anterior"""
        return self._calculate_percentage_change('income', months)
    
    def get_expenses_percentage_change(self, months=1):
        """Calcula a variação percentual de despesas comparado ao período anterior"""
        return self._calculate_percentage_change('expense', months)
    
    def get_balance_percentage_change(self, months=1):
        """Calcula a variação percentual do saldo comparado ao período anterior"""
        current_balance = self.get_month_balance()
        start_date = self.today.replace(day=1)
        end_date = self.today
        return self.get_period_percentage_change(start_date, end_date, 'balance')

    def get_period_percentage_change(self, start_date, end_date, transaction_type='income'):
        """Calcula a variação percentual entre o período atual e o período anterior."""
        if transaction_type == 'income':
            current = self._get_income_range(start_date, end_date)
        elif transaction_type == 'expense':
            current = self._get_expenses_range(start_date, end_date)
        elif transaction_type == 'balance':
            current = self._get_income_range(start_date, end_date) - self._get_expenses_range(start_date, end_date)
        else:
            raise ValueError(f'Unsupported transaction type: {transaction_type}')

        prev_duration_days = (end_date - start_date).days + 1
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=prev_duration_days - 1)

        if transaction_type == 'income':
            previous = self._get_income_range(prev_start_date, prev_end_date)
        elif transaction_type == 'expense':
            previous = self._get_expenses_range(prev_start_date, prev_end_date)
        else:
            previous = self._get_income_range(prev_start_date, prev_end_date) - self._get_expenses_range(prev_start_date, prev_end_date)

        if previous == 0:
            return 0 if current == 0 else 100

        return round(((current - previous) / previous) * 100, 1)

    # Private methods
    
    def _get_total_income(self):
        """Total de receitas de todos os tempos"""
        total = Transaction.objects.filter(
            user=self.user,
            type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return total
    
    def _get_total_expenses(self):
        """Total de despesas de todos os tempos"""
        total = Transaction.objects.filter(
            user=self.user,
            type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return total
    
    def _get_income_range(self, start_date, end_date):
        """Receitas em um período específico"""
        total = Transaction.objects.filter(
            user=self.user,
            type='income',
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return total
    
    def _get_expenses_range(self, start_date, end_date):
        """Despesas em um período específico"""
        total = Transaction.objects.filter(
            user=self.user,
            type='expense',
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return total
    
    def _get_period_start_date(self, period):
        """Retorna a data de início baseada no período"""
        if period == 'month':
            return self.today.replace(day=1)
        elif period == 'quarter':
            quarter = (self.today.month - 1) // 3
            return self.today.replace(month=quarter * 3 + 1, day=1)
        elif period == 'year':
            return self.today.replace(month=1, day=1)
        elif period == '6months':
            return self.today - timedelta(days=180)
        else:
            return self.today.replace(day=1)
    
    def _calculate_percentage_change(self, transaction_type, months=1):
        """Calcula variação percentual entre períodos"""
        # Current period
        start_date = self.today.replace(day=1)
        if transaction_type == 'income':
            current = self._get_income_range(start_date, self.today)
        else:
            current = self._get_expenses_range(start_date, self.today)
        
        # Previous period
        prev_month_start = (start_date - timedelta(days=1)).replace(day=1)
        if start_date.month == 1:
            prev_month_end = (start_date.replace(year=start_date.year - 1, month=12))
        else:
            prev_month_end = start_date - timedelta(days=1)
        
        if transaction_type == 'income':
            previous = self._get_income_range(prev_month_start, prev_month_end)
        else:
            previous = self._get_expenses_range(prev_month_start, prev_month_end)
        
        if previous == 0:
            return 0 if current == 0 else 100
        
        return round(((current - previous) / previous) * 100, 1)


def format_currency(value):
    """Formata valor como moeda brasileira"""
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def get_dashboard_context(user):
    """Retorna o contexto completo do dashboard para uma view"""
    calculator = DashboardCalculator(user)
    
    return {
        'total_balance': calculator.get_total_balance(),
        'total_income': calculator.get_total_income(),
        'total_expenses': calculator.get_total_expenses(),
        'current_month_income': calculator.get_current_month_income(),
        'current_month_expenses': calculator.get_current_month_expenses(),
        'savings': calculator.get_savings(),
        'monthly_trend': calculator.get_monthly_trend(),
        'expenses_by_category': calculator.get_expenses_by_category(),
        'recent_transactions': calculator.get_recent_transactions(),
        'income_change': calculator.get_income_percentage_change(),
        'expenses_change': calculator.get_expenses_percentage_change(),
        'balance_change': calculator.get_balance_percentage_change(),
    }
