# categories/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count
from .models import Category
import json

# Importar Transaction apenas se o app existir
try:
    from transactions.models import Transaction
    HAS_TRANSACTIONS = True
except ImportError:
    HAS_TRANSACTIONS = False

@login_required
def categories_page(request):
    """Renderiza a página de gerenciamento de categorias"""
    return render(request, 'categories/categories.html')

@login_required
def api_categories(request):
    """API endpoint para listar categorias do usuário"""
    try:
        categories = Category.objects.filter(user=request.user).order_by('name')
        
        categories_data = []
        for cat in categories:
            # Calcular gastos da categoria (se houver modelo de transações)
            total_spent = 0
            if HAS_TRANSACTIONS:
                total_spent_result = Transaction.objects.filter(
                    user=request.user,
                    category=cat,
                    type='expense'
                ).aggregate(total=Sum('amount'))['total']
                total_spent = float(total_spent_result) if total_spent_result else 0
            
            categories_data.append({
                'id': cat.id,
                'name': cat.name,
                'type': cat.type,
                'icon': cat.icon,
                'color': getattr(cat, 'color', '#8A4FFF'),
                'description': cat.description or '',
                'is_default': cat.is_default,
                'total_spent': total_spent,
                'budget': float(getattr(cat, 'budget', 0)),
                'created_at': cat.created_at.isoformat() if cat.created_at else None
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

@login_required
def api_categories_summary(request):
    """API endpoint para estatísticas das categorias"""
    try:
        categories = Category.objects.filter(user=request.user)
        
        # Categoria mais usada (com mais transações)
        most_used = None
        if HAS_TRANSACTIONS:
            most_used_data = Transaction.objects.filter(
                user=request.user,
                category__isnull=False
            ).values('category__name').annotate(
                count=Count('id')
            ).order_by('-count').first()
            
            if most_used_data:
                most_used = most_used_data['category__name']
        
        # Total gasto em despesas por categorias
        total_spent = 0
        if HAS_TRANSACTIONS:
            total_spent_result = Transaction.objects.filter(
                user=request.user,
                type='expense'
            ).aggregate(total=Sum('amount'))['total']
            total_spent = float(total_spent_result) if total_spent_result else 0
        
        return JsonResponse({
            'success': True,
            'total_categories': categories.count(),
            'most_used_category': most_used or '-',
            'total_spent': total_spent
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_categories_create(request):
    """API endpoint para criar nova categoria"""
    try:
        data = json.loads(request.body)
        
        # Validação de campos obrigatórios
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'O nome da categoria é obrigatório'
            }, status=400)
        
        # Verificar se categoria já existe para o usuário
        if Category.objects.filter(user=request.user, name__iexact=name).exists():
            return JsonResponse({
                'success': False,
                'error': f'Já existe uma categoria com o nome "{name}"'
            }, status=400)
        
        # Criar categoria
        category = Category.objects.create(
            user=request.user,
            name=name,
            type=data.get('type', 'expense'),
            icon=data.get('icon', '📌'),
            description=data.get('description', ''),
            is_default=False
        )
        
        # Se houver campo color no modelo, adicionar
        if hasattr(category, 'color') and 'color' in data:
            category.color = data.get('color', '#8A4FFF')
            category.save()
        
        # Se houver campo budget, adicionar
        if hasattr(category, 'budget') and 'budget' in data:
            try:
                category.budget = float(data.get('budget', 0))
                category.save()
            except (ValueError, TypeError):
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Categoria criada com sucesso',
            'category': {
                'id': category.id,
                'name': category.name,
                'type': category.type,
                'icon': category.icon,
                'color': getattr(category, 'color', '#8A4FFF'),
                'description': category.description,
                'is_default': category.is_default,
                'budget': float(getattr(category, 'budget', 0)),
                'total_spent': 0
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["PUT", "POST"])
@csrf_exempt
def api_categories_update(request, category_id):
    """API endpoint para atualizar categoria existente"""
    try:
        category = Category.objects.get(id=category_id, user=request.user)
        data = json.loads(request.body)
        
        # Atualizar campos
        if 'name' in data:
            new_name = data['name'].strip()
            if new_name and new_name != category.name:
                # Verificar se novo nome já existe
                if Category.objects.filter(user=request.user, name__iexact=new_name).exclude(id=category_id).exists():
                    return JsonResponse({
                        'success': False,
                        'error': f'Já existe uma categoria com o nome "{new_name}"'
                    }, status=400)
                category.name = new_name
        
        if 'icon' in data:
            category.icon = data['icon']
        
        if 'type' in data and data['type'] in ['income', 'expense']:
            category.type = data['type']
        
        if 'description' in data:
            category.description = data['description']
        
        if hasattr(category, 'color') and 'color' in data:
            category.color = data['color']
        
        if hasattr(category, 'budget') and 'budget' in data:
            try:
                category.budget = float(data['budget'])
            except (ValueError, TypeError):
                pass
        
        category.save()
        
        # Calcular total gasto
        total_spent = 0
        if HAS_TRANSACTIONS:
            total_spent_result = Transaction.objects.filter(
                user=request.user,
                category=category,
                type='expense'
            ).aggregate(total=Sum('amount'))['total']
            total_spent = float(total_spent_result) if total_spent_result else 0
        
        return JsonResponse({
            'success': True,
            'message': 'Categoria atualizada com sucesso',
            'category': {
                'id': category.id,
                'name': category.name,
                'type': category.type,
                'icon': category.icon,
                'color': getattr(category, 'color', '#8A4FFF'),
                'description': category.description,
                'is_default': category.is_default,
                'budget': float(getattr(category, 'budget', 0)),
                'total_spent': total_spent
            }
        })
        
    except Category.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Categoria não encontrada'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def api_categories_delete(request, category_id):
    """API endpoint para deletar categoria"""
    try:
        category = Category.objects.get(id=category_id, user=request.user)
        
        # Impedir deleção de categorias padrão
        if category.is_default:
            return JsonResponse({
                'success': False,
                'error': 'Não é possível excluir categorias padrão do sistema'
            }, status=400)
        
        category_name = category.name
        category.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Categoria "{category_name}" excluída com sucesso'
        })
        
    except Category.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Categoria não encontrada'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)