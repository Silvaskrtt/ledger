from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Category

@login_required
def api_categories(request):
    """API endpoint for categories"""
    categories = Category.objects.filter(user=request.user).values('id', 'name', 'type', 'icon')
    return JsonResponse({'categories': list(categories)})
