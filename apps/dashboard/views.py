from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal

from .utils import DashboardCalculator, get_dashboard_context, format_currency


@login_required
@require_http_methods(["GET"])
def dashboard_summary(request):
    """
    Retorna um resumo completo do dashboard em JSON
    GET /api/dashboard/summary/
    """
    period = request.GET.get('period', 'month')
    calculator = DashboardCalculator(request.user)

    start_date = calculator._get_period_start_date(period)
    end_date = calculator.today

    period_income = calculator._get_income_range(start_date, end_date)
    period_expenses = calculator._get_expenses_range(start_date, end_date)
    period_balance = period_income - period_expenses
    period_savings = period_balance
    savings_rate = float((period_savings / period_income * 100)) if period_income > 0 else 0.0

    data = {
        # Totais do período selecionado
        'total_balance': float(period_balance),
        'total_income': float(period_income),
        'total_expenses': float(period_expenses),
        'period': period,
        'period_start': start_date.isoformat(),
        'period_end': end_date.isoformat(),

        # Dados do mês atual para fallback e comparações
        'current_month_income': float(calculator.get_current_month_income()),
        'current_month_expenses': float(calculator.get_current_month_expenses()),
        'savings': float(period_savings),
        'savings_rate': round(savings_rate, 1),

        # Variações percentuais relativas ao período selecionado
        'income_change': calculator.get_period_percentage_change(start_date, end_date, 'income'),
        'expenses_change': calculator.get_period_percentage_change(start_date, end_date, 'expense'),
        'balance_change': calculator.get_period_percentage_change(start_date, end_date, 'balance'),
    }

    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def dashboard_monthly_trend(request):
    """
    Retorna a tendência mensal de receitas e despesas
    GET /api/dashboard/monthly-trend/?months=12
    """
    months = int(request.GET.get('months', 12))
    calculator = DashboardCalculator(request.user)
    
    trend_data = calculator.get_monthly_trend(months=months)
    
    return JsonResponse({
        'data': trend_data
    })


@login_required
@require_http_methods(["GET"])
def dashboard_expenses_by_category(request):
    """
    Retorna despesas agrupadas por categoria
    GET /api/dashboard/expenses-by-category/?period=month
    """
    period = request.GET.get('period', 'month')
    calculator = DashboardCalculator(request.user)
    
    categories_data = calculator.get_expenses_by_category(period=period)
    
    return JsonResponse({
        'data': categories_data
    })


@login_required
@require_http_methods(["GET"])
def dashboard_recent_transactions(request):
    """
    Retorna as transações recentes
    GET /api/dashboard/recent-transactions/?limit=5
    """
    limit = int(request.GET.get('limit', 5))
    calculator = DashboardCalculator(request.user)
    
    transactions_data = calculator.get_recent_transactions(limit=limit)
    
    return JsonResponse({
        'data': transactions_data
    })


@login_required
def dashboard_context_view(request):
    """
    View para renderizar o template do dashboard com contexto completo
    Pode ser usado como fallback ou para primeira carga
    """
    context = get_dashboard_context(request.user)
    
    # Converter Decimal para float para JSON serialization
    def decimal_to_float(obj):
        if isinstance(obj, dict):
            return {k: decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [decimal_to_float(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    context = decimal_to_float(context)
    return render(request, 'dashboard/index.html', context)
