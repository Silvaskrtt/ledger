import json
from datetime import datetime, date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Value, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from .forms import TransactionForm
from .models import Transaction
from .serializers import TransactionSerializer


@login_required
def calendar_page(request):
    return render(request, 'calendar/calendar.html')


@login_required
@require_GET
def api_transactions(request):
    try:
        qs = Transaction.objects.filter(user=request.user)
        transactions = [TransactionSerializer.to_representation(tx) for tx in qs.order_by('-date', '-created_at')]
        return JsonResponse({'success': True, 'transactions': transactions})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_transactions_create(request):
    try:
        data = json.loads(request.body)
        form = TransactionForm(data)
        if not form.is_valid():
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        transaction = form.save(commit=False)
        transaction.user = request.user
        transaction.save()

        return JsonResponse({'success': True, 'transaction': TransactionSerializer.to_representation(transaction)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(['PUT', 'PATCH'])
def api_transactions_update(request, pk):
    try:
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        data = json.loads(request.body)
        form = TransactionForm(data, instance=transaction)

        if not form.is_valid():
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        transaction = form.save()
        return JsonResponse({'success': True, 'transaction': TransactionSerializer.to_representation(transaction)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(['DELETE'])
def api_transactions_delete(request, pk):
    try:
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        transaction.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_GET
def api_monthly_summary(request):
    try:
        year_str = request.GET.get('year')
        month_str = request.GET.get('month')
        
        if not year_str or not month_str:
            return JsonResponse({'success': False, 'error': 'Ano e mês são obrigatórios'}, status=400)
        
        year = int(year_str)
        month = int(month_str)

        if month < 1 or month > 12:
            raise ValueError('Mês inválido')

        start_date = date(year, month, 1)
        previous_qs = Transaction.objects.filter(user=request.user, date__lt=start_date)
        opening_income = previous_qs.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        opening_expense = previous_qs.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
        opening_saving = previous_qs.filter(type='saving').aggregate(total=Sum('amount'))['total'] or 0
        opening_balance = float(opening_income - opening_expense + opening_saving)

        qs = Transaction.objects.filter(
            user=request.user, 
            date__year=year, 
            date__month=month
        )

        # CORREÇÃO DEFINITIVA: Usando Value com output_field e Coalesce para garantir tipo Decimal
        daily_data = qs.values('date').annotate(
            income=Coalesce(
                Sum(Case(
                    When(type='income', then='amount'),
                    default=Value(0, output_field=DecimalField()),
                    output_field=DecimalField()
                )),
                Value(0, output_field=DecimalField())
            ),
            expense=Coalesce(
                Sum(Case(
                    When(type='expense', then='amount'),
                    default=Value(0, output_field=DecimalField()),
                    output_field=DecimalField()
                )),
                Value(0, output_field=DecimalField())
            ),
            saving=Coalesce(
                Sum(Case(
                    When(type='saving', then='amount'),
                    default=Value(0, output_field=DecimalField()),
                    output_field=DecimalField()
                )),
                Value(0, output_field=DecimalField())
            ),
        ).order_by('date')

        summary = {
            'opening_balance': opening_balance,
            'days': [],
            'total_income': 0.0,
            'total_expense': 0.0,
            'total_saving': 0.0,
        }

        balance = opening_balance
        for item in daily_data:
            date = item['date']
            income = float(item['income'] or 0)
            expense = float(item['expense'] or 0)
            saving = float(item['saving'] or 0)
            balance += income - expense + saving
            summary['days'].append({
                'date': date.isoformat(),
                'income': income,
                'expense': expense,
                'saving': saving,
                'balance': balance,
            })
            summary['total_income'] += income
            summary['total_expense'] += expense
            summary['total_saving'] += saving

        return JsonResponse({'success': True, 'summary': summary})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'}, status=500)


@login_required
@require_GET
def api_monthly_balance(request):
    try:
        year_str = request.GET.get('year')
        month_str = request.GET.get('month')
        year = int(year_str) if year_str and year_str.isdigit() else datetime.today().year
        month = int(month_str) if month_str and month_str.isdigit() else datetime.today().month
        if month < 1 or month > 12:
            raise ValueError('Mês inválido')
        qs = Transaction.objects.filter(user=request.user, date__year=year, date__month=month)

        total_income = qs.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        total_expense = qs.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
        total_saving = qs.filter(type='saving').aggregate(total=Sum('amount'))['total'] or 0
        balance = total_income - total_expense + total_saving

        return JsonResponse({
            'success': True,
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'total_saving': float(total_saving),
            'balance': float(balance),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_GET
def api_transactions_filter(request):
    try:
        year_str = request.GET.get('year')
        month_str = request.GET.get('month')
        year = int(year_str) if year_str and year_str.isdigit() else datetime.today().year
        month = int(month_str) if month_str and month_str.isdigit() else datetime.today().month

        if month < 1 or month > 12:
            raise ValueError('Mês inválido')

        start_str = request.GET.get('start')
        end_str = request.GET.get('end')
        start = parse_date(start_str) if start_str else None
        end = parse_date(end_str) if end_str else None

        qs = Transaction.objects.filter(user=request.user)
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        if year and month:
            qs = qs.filter(date__year=year, date__month=month)

        transactions = [TransactionSerializer.to_representation(tx) for tx in qs.order_by('-date', '-created_at')]
        return JsonResponse({'success': True, 'transactions': transactions})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)