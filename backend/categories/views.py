# backend/categories/views.py

import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Category
from .serializers import CategorySerializer

logger = logging.getLogger(__name__)

"""Views para gerenciamento de categorias."""
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Category
from .serializers import CategorySerializer
from django.shortcuts import render

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Retorna apenas categorias do usuário atual
        return Category.objects.filter(user=self.request.user).order_by('type', 'name')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Erro ao listar categorias: {type(e).__name__}: {e}")
            return Response(
                {'detail': 'Erro ao processar requisição'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@login_required(login_url='/accounts/login/')
def categories_management_view(request):
    return render(request, 'categories_management/categories_management.html')