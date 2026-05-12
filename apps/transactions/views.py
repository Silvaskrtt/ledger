from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transaction
from .forms import TransactionForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from datetime import datetime

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 10
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        total_income = sum(t.amount for t in queryset if t.type == 'income')
        total_expense = sum(t.amount for t in queryset if t.type == 'expense')
        context['total_income'] = float(total_income)
        context['total_expense'] = float(total_expense)
        context['balance'] = float(total_income - total_expense)
        
        # Adicionar categorias para o filtro
        categories = Transaction.objects.filter(user=self.request.user)\
            .values_list('category__name', flat=True).distinct()
        context['categories'] = [{'name': cat, 'icon': get_category_icon(cat)} for cat in categories]
        
        return context


@login_required
@require_http_methods(["GET"])
def api_transactions(request):
    """API endpoint for transactions - GET only"""
    try:
        queryset = Transaction.objects.filter(user=request.user).order_by('-date')
        
        # Aplicar filtros
        search = request.GET.get('search', '')
        type_filter = request.GET.get('type', '')
        category = request.GET.get('category', '')
        month = request.GET.get('month', '')
        
        if search:
            queryset = queryset.filter(description__icontains=search)
        if type_filter and type_filter != 'all':
            queryset = queryset.filter(type=type_filter)
        if category and category != 'all':
            queryset = queryset.filter(category__name__icontains=category)
        if month:
            queryset = queryset.filter(date__year=month[:4], date__month=month[5:])
        
        # Paginação
        page = request.GET.get('page', 1)
        paginator = Paginator(queryset, 10)
        
        try:
            current_page = paginator.page(page)
        except:
            current_page = paginator.page(1)
        
        # Preparar dados
        data = []
        for t in current_page:
            data.append({
                'id': t.id,
                'description': t.description,
                'amount': float(t.amount),
                'type': t.type,
                'category': t.category.name,
                'categoryId': t.category.id,
                'date': t.date.strftime('%Y-%m-%d'),
                'notes': t.notes or '',
                'categoryIcon': t.category.icon or get_category_icon(t.category.name),
            })
        
        # Calcular totais
        total_income = sum(float(t.amount) for t in queryset if t.type == 'income')
        total_expense = sum(float(t.amount) for t in queryset if t.type == 'expense')
        balance = total_income - total_expense
        
        return JsonResponse({
            'transactions': data,
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'total_pages': paginator.num_pages,
            'current_page': current_page.number,
            'has_next': current_page.has_next(),
            'has_previous': current_page.has_previous(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_transactions_create(request):
    """API endpoint for creating transactions"""
    try:
        data = json.loads(request.body)
        
        transaction = Transaction.objects.create(
            user=request.user,
            description=data.get('description'),
            amount=Decimal(str(data.get('amount'))),
            type=data.get('type'),
            category_id=data.get('category'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            notes=data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'transaction': {
                'id': transaction.id,
                'description': transaction.description,
                'amount': float(transaction.amount),
                'type': transaction.type,
                'category': transaction.category.name,
                'categoryId': transaction.category.id,
                'date': transaction.date.strftime('%Y-%m-%d'),
                'notes': transaction.notes,
                'categoryIcon': transaction.category.icon or get_category_icon(transaction.category.name),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["PUT", "POST"])
def api_transactions_update(request, pk):
    """API endpoint for updating transactions"""
    try:
        transaction = get_object_or_404(Transaction, id=pk, user=request.user)
        data = json.loads(request.body)
        
        transaction.description = data.get('description', transaction.description)
        transaction.amount = Decimal(str(data.get('amount', transaction.amount)))
        transaction.type = data.get('type', transaction.type)
        if data.get('category'):
            transaction.category_id = data.get('category')
        date_str = data.get('date')
        if date_str:
            transaction.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        transaction.notes = data.get('notes', transaction.notes)
        transaction.save()
        
        return JsonResponse({
            'success': True,
            'transaction': {
                'id': transaction.id,
                'description': transaction.description,
                'amount': float(transaction.amount),
                'type': transaction.type,
                'category': transaction.category.name,
                'categoryId': transaction.category.id,
                'date': transaction.date.strftime('%Y-%m-%d'),
                'notes': transaction.notes,
                'categoryIcon': transaction.category.icon or get_category_icon(transaction.category.name),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def api_transactions_delete(request, pk):
    """API endpoint for deleting transactions"""
    try:
        transaction = get_object_or_404(Transaction, id=pk, user=request.user)
        transaction.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_category_icon(category):
    """Retorna ícone para categoria"""
    icons = {
        'Alimentação': '🍔',
        'Transporte': '🚗',
        'Lazer': '🎮',
        'Moradia': '🏠',
        'Saúde': '💊',
        'Educação': '📚',
        'Trabalho': '💼',
        'Outros': '📌',
    }
    return icons.get(category, '📌')