import json
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Value, Case, When
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
        year = int(request.GET.get('year', datetime.today().year))
        month = int(request.GET.get('month', datetime.today().month))
        qs = Transaction.objects.filter(user=request.user, date__year=year, date__month=month)

        summary = {
            'days': [],
            'total_income': 0.0,
            'total_expense': 0.0,
            'total_saving': 0.0,
        }

        daily_data = qs.values('date').annotate(
            income=Sum(Case(When(type='income', then='amount'), default=Value(0))),
            expense=Sum(Case(When(type='expense', then='amount'), default=Value(0))),
            saving=Sum(Case(When(type='saving', then='amount'), default=Value(0))),
        ).order_by('date')

        balance = 0
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
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_GET
def api_monthly_balance(request):
    try:
        year = int(request.GET.get('year', datetime.today().year))
        month = int(request.GET.get('month', datetime.today().month))
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
        year = int(request.GET.get('year', datetime.today().year))
        month = int(request.GET.get('month', datetime.today().month))
        start = parse_date(request.GET.get('start'))
        end = parse_date(request.GET.get('end'))

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
