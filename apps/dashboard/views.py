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
    calculator = DashboardCalculator(request.user)
    
    data = {
        'total_balance': float(calculator.get_total_balance()),
        'total_income': float(calculator.get_total_income()),
        'total_expenses': float(calculator.get_total_expenses()),
        'current_month_income': float(calculator.get_current_month_income()),
        'current_month_expenses': float(calculator.get_current_month_expenses()),
        'savings': float(calculator.get_savings()),
        'income_change': calculator.get_income_percentage_change(),
        'expenses_change': calculator.get_expenses_percentage_change(),
        'balance_change': calculator.get_balance_percentage_change(),
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
