import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from .models import Goal
from .forms import GoalForm

@login_required
@ensure_csrf_cookie
def goals_page(request):
    """Renderiza a página de metas"""
    return render(request, 'goals/goals.html')

@login_required
def get_goals(request):
    """Retorna todas as metas do usuário via JSON"""
    goals = Goal.objects.filter(user=request.user)
    
    goals_data = []
    for goal in goals:
        goals_data.append({
            'id': goal.id,
            'title': goal.title,
            'description': goal.description or '',
            'target': float(goal.target),
            'current': float(goal.current),
            'deadline': goal.deadline.isoformat(),
            'icon': goal.icon,
            'completed': goal.completed,
            'created_at': goal.created_at.isoformat(),
            'progress_percentage': goal.progress_percentage,
            'remaining_amount': float(goal.remaining_amount),
            'days_remaining': goal.days_remaining,
            'deadline_status': goal.deadline_status,
            'deadline_text': goal.deadline_text,
            'is_completable': goal.is_completable
        })
    
    return JsonResponse({'success': True, 'goals': goals_data})

@login_required
@require_http_methods(['POST'])
def create_goal(request):
    """Cria uma nova meta"""
    try:
        data = json.loads(request.body)
        form = GoalForm(data)
        
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Meta criada com sucesso!',
                'goal': {
                    'id': goal.id,
                    'title': goal.title,
                    'description': goal.description or '',
                    'target': float(goal.target),
                    'current': float(goal.current),
                    'deadline': goal.deadline.isoformat(),
                    'icon': goal.icon,
                    'completed': goal.completed,
                    'created_at': goal.created_at.isoformat(),
                    'progress_percentage': goal.progress_percentage,
                    'remaining_amount': float(goal.remaining_amount),
                    'days_remaining': goal.days_remaining,
                    'deadline_status': goal.deadline_status,
                    'deadline_text': goal.deadline_text,
                    'is_completable': goal.is_completable
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': dict(form.errors)
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(['PUT', 'POST'])
def update_goal(request, goal_id):
    """Atualiza uma meta existente"""
    try:
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        data = json.loads(request.body)
        
        # Verificar se a meta pode ser marcada como concluída automaticamente
        if data.get('current') and float(data.get('current')) >= float(goal.target):
            data['completed'] = True
        
        form = GoalForm(data, instance=goal)
        
        if form.is_valid():
            goal = form.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Meta atualizada com sucesso!',
                'goal': {
                    'id': goal.id,
                    'title': goal.title,
                    'description': goal.description or '',
                    'target': float(goal.target),
                    'current': float(goal.current),
                    'deadline': goal.deadline.isoformat(),
                    'icon': goal.icon,
                    'completed': goal.completed,
                    'created_at': goal.created_at.isoformat(),
                    'progress_percentage': goal.progress_percentage,
                    'remaining_amount': float(goal.remaining_amount),
                    'days_remaining': goal.days_remaining,
                    'deadline_status': goal.deadline_status,
                    'deadline_text': goal.deadline_text,
                    'is_completable': goal.is_completable
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': dict(form.errors)
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(['DELETE'])
def delete_goal(request, goal_id):
    """Exclui uma meta"""
    try:
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        goal.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Meta excluída com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(['POST'])
def complete_goal(request, goal_id):
    """Marca uma meta como concluída"""
    try:
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        goal.completed = True
        goal.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Parabéns! Meta concluída com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def get_goal_stats(request):
    """Retorna estatísticas das metas"""
    goals = Goal.objects.filter(user=request.user)
    
    active_goals = goals.filter(completed=False).count()
    completed_goals = goals.filter(completed=True).count()
    
    total_saved = sum(goal.current for goal in goals)
    
    # Progresso médio
    if goals.exists():
        avg_progress = sum(goal.progress_percentage for goal in goals) / goals.count()
    else:
        avg_progress = 0
    
    return JsonResponse({
        'success': True,
        'stats': {
            'active_goals': active_goals,
            'completed_goals': completed_goals,
            'total_saved': float(total_saved),
            'total_progress': round(avg_progress, 1),
            'total_goals': goals.count()
        }
    })