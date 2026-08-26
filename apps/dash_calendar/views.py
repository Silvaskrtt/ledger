import json
from datetime import datetime, date as date_cls
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Value, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from .forms import TransactionForm
from .models import Transaction, MonthlyBudget
from .serializers import TransactionSerializer

# Import do app categories
try:
    from categories.models import Category
    HAS_CATEGORIES = True
except ImportError:
    HAS_CATEGORIES = False


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
        
        # Validar categoria se estiver usando o app categories
        if HAS_CATEGORIES:
            category_name = data.get('category', '')
            if category_name:
                # Verifica se a categoria existe para o usuário, se não, cria
                category, created = Category.objects.get_or_create(
                    user=request.user,
                    name=category_name,
                    defaults={
                        'type': data.get('type', 'expense'),
                        'icon': '📌',
                        'is_default': False
                    }
                )
                # Se a categoria foi criada ou existe, usamos o nome
                data['category'] = category.name
        
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
        
        # Validar categoria se estiver usando o app categories
        if HAS_CATEGORIES:
            category_name = data.get('category', '')
            if category_name:
                # Verifica se a categoria existe para o usuário, se não, cria
                category, created = Category.objects.get_or_create(
                    user=request.user,
                    name=category_name,
                    defaults={
                        'type': data.get('type', 'expense'),
                        'icon': '📌',
                        'is_default': False
                    }
                )
                # Se a categoria foi criada ou existe, usamos o nome
                data['category'] = category.name

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

        start_date = date_cls(year, month, 1)
        previous_qs = Transaction.objects.filter(user=request.user, date__lt=start_date)
        opening_income = previous_qs.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        opening_expense = previous_qs.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
        opening_saving = previous_qs.filter(type='saving').aggregate(total=Sum('amount'))['total'] or 0
        opening_card = previous_qs.filter(type='card').aggregate(total=Sum('amount'))['total'] or 0
        opening_balance = float(opening_income - opening_expense - opening_card - opening_saving)

        qs = Transaction.objects.filter(
            user=request.user, 
            date__year=year, 
            date__month=month
        )

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
            card=Coalesce(
                Sum(Case(
                    When(type='card', then='amount'),
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
            'total_saving': float(opening_saving),
            'monthly_saving': 0.0,
            'total_card': 0.0,
        }

        balance = opening_balance
        for item in daily_data:
            date = item['date']
            income = float(item['income'] or 0)
            expense = float(item['expense'] or 0)
            saving = float(item['saving'] or 0)
            card = float(item['card'] or 0)
            balance += income - expense - card - saving
            summary['days'].append({
                'date': date.isoformat(),
                'income': income,
                'expense': expense,
                'saving': saving,
                'card': card,
                'balance': balance,
            })
            summary['total_income'] += income
            summary['total_expense'] += expense
            summary['total_saving'] += saving
            summary['monthly_saving'] += saving
            summary['total_card'] += card

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
        monthly_saving = qs.filter(type='saving').aggregate(total=Sum('amount'))['total'] or 0
        previous_saving = Transaction.objects.filter(
            user=request.user,
            date__lt=date_cls(year, month, 1),
            type='saving',
        ).aggregate(total=Sum('amount'))['total'] or 0
        total_saving = previous_saving + monthly_saving
        total_card = qs.filter(type='card').aggregate(total=Sum('amount'))['total'] or 0
        balance = total_income - total_expense - total_card - monthly_saving

        return JsonResponse({
            'success': True,
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'total_saving': float(total_saving),
            'monthly_saving': float(monthly_saving),
            'total_card': float(total_card),
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


# ============ API DE CATEGORIAS PARA O CALENDÁRIO ============

@login_required
@require_GET
def api_categories_list(request):
    """Lista as categorias do usuário para usar no calendário"""
    try:
        if not HAS_CATEGORIES:
            # Fallback para categorias fixas se o app categories não estiver disponível
            categories = [
                {'id': 'food', 'name': 'Alimentação', 'icon': '🍔', 'type': 'expense'},
                {'id': 'home', 'name': 'Moradia', 'icon': '🏠', 'type': 'expense'},
                {'id': 'transport', 'name': 'Transporte', 'icon': '🚗', 'type': 'expense'},
                {'id': 'fun', 'name': 'Lazer', 'icon': '🎮', 'type': 'expense'},
                {'id': 'work', 'name': 'Trabalho', 'icon': '💼', 'type': 'expense'},
                {'id': 'edu', 'name': 'Educação', 'icon': '📚', 'type': 'expense'},
                {'id': 'health', 'name': 'Saúde', 'icon': '🏥', 'type': 'expense'},
                {'id': 'salary', 'name': 'Salário', 'icon': '💰', 'type': 'income'},
            ]
            return JsonResponse({'success': True, 'categories': categories})
        
        categories = Category.objects.filter(user=request.user).order_by('name')
        
        categories_data = []
        for cat in categories:
            categories_data.append({
                'id': cat.id,
                'name': cat.name,
                'icon': cat.icon or '📌',
                'color': getattr(cat, 'color', '#8A4FFF'),
                'type': cat.type,
                'is_default': cat.is_default,
                'description': cat.description or '',
            })
        
        return JsonResponse({
            'success': True,
            'categories': categories_data,
            'total': len(categories_data)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============ VIEWS DE BUDGET ============

@login_required
@require_GET
def api_budget_get(request):
    try:
        year_str = request.GET.get('year')
        month_str = request.GET.get('month')
        
        if not year_str or not month_str:
            today = datetime.today()
            year = today.year
            month = today.month
        else:
            year = int(year_str)
            month = int(month_str)
            
            if month < 1 or month > 12:
                raise ValueError('Mês inválido')
        
        budget = MonthlyBudget.objects.filter(
            user=request.user,
            year=year,
            month=month
        ).first()
        
        # Buscar categorias do usuário para preencher o resumo
        user_categories = []
        if HAS_CATEGORIES:
            categories_qs = Category.objects.filter(user=request.user, type='expense')
            for cat in categories_qs:
                user_categories.append(cat.name)
        
        if budget:
            # Garantir que todas as categorias do usuário estejam no budget
            categories_data = budget.categories.copy() if budget.categories else {}
            for cat_name in user_categories:
                if cat_name not in categories_data:
                    categories_data[cat_name] = 0
            
            return JsonResponse({
                'success': True,
                'budget': {
                    'id': budget.id,
                    'year': budget.year,
                    'month': budget.month,
                    'categories': categories_data,
                    'extras': budget.extras,
                    'total_planned': float(budget.total_planned),
                    'divisor': budget.divisor,
                    'daily_goal': budget.get_daily_goal(),
                },
                'user_categories': user_categories
            })
        else:
            # Criar categorias vazias para o usuário
            categories_data = {}
            for cat_name in user_categories:
                categories_data[cat_name] = 0
            
            return JsonResponse({
                'success': True,
                'budget': {
                    'year': year,
                    'month': month,
                    'categories': categories_data,
                    'extras': [],
                    'total_planned': 0,
                    'divisor': 30,
                    'daily_goal': 0,
                },
                'user_categories': user_categories
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_budget_save(request):
    try:
        data = json.loads(request.body)
        
        year = data.get('year')
        month = data.get('month')
        
        if not year or not month:
            return JsonResponse({'success': False, 'error': 'Ano e mês são obrigatórios'}, status=400)
        
        budget, created = MonthlyBudget.objects.get_or_create(
            user=request.user,
            year=year,
            month=month,
            defaults={
                'categories': {},
                'extras': [],
                'total_planned': 0,
                'divisor': 30
            }
        )
        
        budget.categories = data.get('categories', {})
        budget.extras = data.get('extras', [])
        budget.divisor = data.get('divisor', 30)
        
        total_categories = sum(float(v or 0) for v in budget.categories.values())
        total_extras = sum(float(e.get('amount', 0)) for e in budget.extras)
        budget.total_planned = total_categories + total_extras
        
        budget.save()
        
        return JsonResponse({
            'success': True,
            'budget': {
                'id': budget.id,
                'year': budget.year,
                'month': budget.month,
                'categories': budget.categories,
                'extras': budget.extras,
                'total_planned': float(budget.total_planned),
                'divisor': budget.divisor,
                'daily_goal': budget.get_daily_goal(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)