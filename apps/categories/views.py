from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Category
import json

@login_required
def api_categories(request):
    """API endpoint for categories"""
    categories = Category.objects.filter(user=request.user).values('id', 'name', 'type', 'icon')
    return JsonResponse({'categories': list(categories)})

@login_required
def api_categories_create(request):
    """API endpoint for creating categories"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category = Category.objects.create(
                user=request.user,
                name=data.get('name'),
                icon=data.get('icon', '📌'),
                type=data.get('type', 'expense')
            )
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'type': category.type,
                    'icon': category.icon
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
