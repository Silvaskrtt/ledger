# reports/views.py
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
import csv
from io import StringIO, BytesIO

from transactions.models import Transaction
from categories.models import Category
from .models import ReportHistory

@login_required
def reports_page(request):
    """Renderiza a página de relatórios"""
    return render(request, 'reports/reports.html')

@login_required
def api_report_summary(request):
    """API endpoint para resumo do relatório"""
    try:
        period = request.GET.get('period', 'month')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Calcular datas baseado no período
        today = timezone.now().date()
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            if period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            elif period == 'month':
                start_date = today.replace(day=1)
                end_date = today
            elif period == 'quarter':
                quarter_start_month = ((today.month - 1) // 3) * 3 + 1
                start_date = today.replace(month=quarter_start_month, day=1)
                end_date = today
            elif period == 'year':
                start_date = today.replace(month=1, day=1)
                end_date = today
            else:
                start_date = today.replace(day=1)
                end_date = today
        
        # Filtrar transações
        transactions = Transaction.objects.filter(
            user=request.user,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calcular totais
        total_income = transactions.filter(type='income').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        total_expense = transactions.filter(type='expense').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        balance = total_income - total_expense
        savings_rate = float((balance / total_income * 100)) if total_income > 0 else 0
        
        # Calcular tendências (comparar com período anterior)
        prev_duration = (end_date - start_date).days + 1
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=prev_duration - 1)
        
        prev_transactions = Transaction.objects.filter(
            user=request.user,
            date__gte=prev_start_date,
            date__lte=prev_end_date
        )
        
        prev_income = prev_transactions.filter(type='income').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        prev_expense = prev_transactions.filter(type='expense').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        
        income_change = float(((total_income - prev_income) / prev_income * 100)) if prev_income > 0 else 0
        expense_change = float(((total_expense - prev_expense) / prev_expense * 100)) if prev_expense > 0 else 0
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_income': float(total_income),
                'total_expense': float(total_expense),
                'balance': float(balance),
                'savings_rate': round(savings_rate, 1),
                'income_change': round(income_change, 1),
                'expense_change': round(expense_change, 1),
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_monthly_trend(request):
    """API endpoint para tendência mensal"""
    try:
        months = int(request.GET.get('months', 12))
        today = timezone.now().date()
        
        data = []
        for i in range(months - 1, -1, -1):
            # Calcular mês
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1
            
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            # Buscar transações do mês
            transactions = Transaction.objects.filter(
                user=request.user,
                date__gte=start_date,
                date__lte=end_date
            )
            
            income = transactions.filter(type='income').aggregate(
                total=Sum('amount'))['total'] or Decimal('0')
            expense = transactions.filter(type='expense').aggregate(
                total=Sum('amount'))['total'] or Decimal('0')
            
            data.append({
                'month': start_date.strftime('%b/%y'),
                'income': float(income),
                'expense': float(expense),
                'balance': float(income - expense)
            })
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_expenses_by_category(request):
    """API endpoint para despesas por categoria"""
    try:
        period = request.GET.get('period', 'month')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        today = timezone.now().date()
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            if period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            elif period == 'month':
                start_date = today.replace(day=1)
                end_date = today
            elif period == 'quarter':
                quarter_start_month = ((today.month - 1) // 3) * 3 + 1
                start_date = today.replace(month=quarter_start_month, day=1)
                end_date = today
            elif period == 'year':
                start_date = today.replace(month=1, day=1)
                end_date = today
            else:
                start_date = today.replace(day=1)
                end_date = today
        
        # Buscar categorias de despesa
        categories = Category.objects.filter(user=request.user, type='expense')
        
        data = []
        total = Decimal('0')
        
        for category in categories:
            amount = Transaction.objects.filter(
                user=request.user,
                category=category,
                type='expense',
                date__gte=start_date,
                date__lte=end_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            if amount > 0:
                data.append({
                    'name': category.name,
                    'amount': float(amount),
                    'icon': category.icon,
                    'color': category.color
                })
                total += amount
        
        # Calcular porcentagens
        for item in data:
            item['percentage'] = round((item['amount'] / float(total)) * 100, 1) if total > 0 else 0
        
        return JsonResponse({'success': True, 'data': sorted(data, key=lambda x: x['amount'], reverse=True)})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_top_expenses(request):
    """API endpoint para maiores despesas"""
    try:
        limit = int(request.GET.get('limit', 5))
        period = request.GET.get('period', 'month')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        today = timezone.now().date()
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            if period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            elif period == 'month':
                start_date = today.replace(day=1)
                end_date = today
            elif period == 'quarter':
                quarter_start_month = ((today.month - 1) // 3) * 3 + 1
                start_date = today.replace(month=quarter_start_month, day=1)
                end_date = today
            elif period == 'year':
                start_date = today.replace(month=1, day=1)
                end_date = today
            else:
                start_date = today.replace(day=1)
                end_date = today
        
        expenses = Transaction.objects.filter(
            user=request.user,
            type='expense',
            date__gte=start_date,
            date__lte=end_date
        ).select_related('category').order_by('-amount')[:limit]
        
        data = []
        for idx, expense in enumerate(expenses):
            data.append({
                'rank': idx + 1,
                'id': expense.id,
                'description': expense.description,
                'amount': float(expense.amount),
                'date': expense.date.strftime('%d/%m/%Y'),
                'category': expense.category.name if expense.category else 'Sem categoria',
                'icon': expense.category.icon if expense.category else '📌'
            })
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_monthly_summary(request):
    """API endpoint para resumo mensal"""
    try:
        year = int(request.GET.get('year', timezone.now().year))
        
        data = []
        for month in range(1, 13):
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            transactions = Transaction.objects.filter(
                user=request.user,
                date__gte=start_date,
                date__lte=end_date
            )
            
            income = transactions.filter(type='income').aggregate(
                total=Sum('amount'))['total'] or Decimal('0')
            expense = transactions.filter(type='expense').aggregate(
                total=Sum('amount'))['total'] or Decimal('0')
            balance = income - expense
            savings_rate = float((balance / income * 100)) if income > 0 else 0
            
            data.append({
                'month': start_date.strftime('%B'),
                'month_num': month,
                'income': float(income),
                'expense': float(expense),
                'balance': float(balance),
                'savings_rate': round(savings_rate, 1)
            })
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_export_report(request):
    """API endpoint para exportar relatório"""
    try:
        data = json.loads(request.body)
        format_type = data.get('format', 'csv')
        period = data.get('period', 'month')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Buscar dados do relatório
        report_data = get_report_data(request.user, period, start_date, end_date)
        
        # Registrar histórico
        ReportHistory.objects.create(
            user=request.user,
            report_type=period,
            format=format_type,
            period_start=report_data['period_start'],
            period_end=report_data['period_end'],
            total_income=Decimal(str(report_data['total_income'])),
            total_expense=Decimal(str(report_data['total_expense'])),
            balance=Decimal(str(report_data['balance']))
        )
        
        if format_type == 'csv':
            return export_csv(report_data)
        elif format_type == 'json':
            return export_json(report_data)
        else:
            return JsonResponse({'error': 'Formato não suportado'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_report_data(user, period, start_date=None, end_date=None):
    """Coleta dados para o relatório"""
    today = timezone.now().date()
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        if period == 'week':
            start = today - timedelta(days=today.weekday())
            end = today
        elif period == 'month':
            start = today.replace(day=1)
            end = today
        elif period == 'quarter':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start = today.replace(month=quarter_start_month, day=1)
            end = today
        elif period == 'year':
            start = today.replace(month=1, day=1)
            end = today
        else:
            start = today.replace(day=1)
            end = today
    
    transactions = Transaction.objects.filter(
        user=user,
        date__gte=start,
        date__lte=end
    )
    
    total_income = transactions.filter(type='income').aggregate(
        total=Sum('amount'))['total'] or Decimal('0')
    total_expense = transactions.filter(type='expense').aggregate(
        total=Sum('amount'))['total'] or Decimal('0')
    
    # Despesas por categoria
    categories_data = []
    categories = Category.objects.filter(user=user, type='expense')
    for cat in categories:
        amount = transactions.filter(category=cat, type='expense').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        if amount > 0:
            categories_data.append({
                'name': cat.name,
                'amount': float(amount),
                'icon': cat.icon,
                'color': cat.color
            })
    
    # Transações
    transactions_list = []
    for t in transactions.order_by('-date')[:50]:
        transactions_list.append({
            'date': t.date.strftime('%d/%m/%Y'),
            'description': t.description,
            'category': t.category.name if t.category else 'Sem categoria',
            'amount': float(t.amount),
            'type': 'Receita' if t.type == 'income' else 'Despesa'
        })
    
    return {
        'period_start': start,
        'period_end': end,
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'balance': float(total_income - total_expense),
        'savings_rate': round(float((total_income - total_expense) / total_income * 100), 1) if total_income > 0 else 0,
        'categories': categories_data,
        'transactions': transactions_list,
        'generated_at': timezone.now().isoformat(),
        'user': user.username
    }

def export_csv(report_data):
    """Exporta relatório como CSV"""
    output = StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Cabeçalho do relatório
    writer.writerow(['MyLedger - Relatório Financeiro'])
    writer.writerow([f'Período: {report_data["period_start"]} a {report_data["period_end"]}'])
    writer.writerow([f'Gerado em: {report_data["generated_at"]}'])
    writer.writerow([])
    
    # Resumo
    writer.writerow(['RESUMO DO PERÍODO'])
    writer.writerow(['Total de Receitas', f'R$ {report_data["total_income"]:.2f}'])
    writer.writerow(['Total de Despesas', f'R$ {report_data["total_expense"]:.2f}'])
    writer.writerow(['Saldo', f'R$ {report_data["balance"]:.2f}'])
    writer.writerow(['Taxa de Economia', f'{report_data["savings_rate"]}%'])
    writer.writerow([])
    
    # Despesas por categoria
    writer.writerow(['DESPESAS POR CATEGORIA'])
    writer.writerow(['Categoria', 'Valor', 'Percentual'])
    total = sum(c['amount'] for c in report_data['categories'])
    for cat in report_data['categories']:
        percentage = (cat['amount'] / total * 100) if total > 0 else 0
        writer.writerow([cat['name'], f'R$ {cat["amount"]:.2f}', f'{percentage:.1f}%'])
    writer.writerow([])
    
    # Transações
    writer.writerow(['TRANSAÇÕES'])
    writer.writerow(['Data', 'Descrição', 'Categoria', 'Valor', 'Tipo'])
    for t in report_data['transactions']:
        writer.writerow([t['date'], t['description'], t['category'], f'R$ {t["amount"]:.2f}', t['type']])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="relatorio_{report_data["period_start"]}_{report_data["period_end"]}.csv"'
    return response

def export_json(report_data):
    """Exporta relatório como JSON"""
    response = HttpResponse(json.dumps(report_data, ensure_ascii=False, indent=2), 
                           content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="relatorio_{report_data["period_start"]}_{report_data["period_end"]}.json"'
    return response