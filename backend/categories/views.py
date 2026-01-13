import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Category
from .serializers import CategorySerializer

logger = logging.getLogger(__name__)


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retorna categorias do usuário, organizadas hierarquicamente"""
        user = self.request.user
        
        # Filtrar por tipo se especificado
        type_filter = self.request.query_params.get('type', None)
        queryset = Category.objects.filter(user=user)
        
        if type_filter in ['IN', 'OUT']:
            queryset = queryset.filter(type=type_filter)
        
        # Ordenar por tipo e nome
        return queryset.order_by('type', 'name')
    
    def perform_create(self, serializer):
        """Salva a categoria com o usuário atual"""
        serializer.save(user=self.request.user)
    
    def get_serializer_context(self):
        """Garante que o contexto tenha o request"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Override para verificar subcategorias antes de deletar"""
        instance = self.get_object()
        
        # Verificar se tem subcategorias
        if instance.subcategories.exists():
            return Response(
                {'detail': 'Não é possível excluir uma categoria que possui subcategorias.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se está em uso (transações)
        # Aqui você pode adicionar a verificação com transações
        # from transactions.models import Transaction
        # if Transaction.objects.filter(category=instance).exists():
        #     return Response(...)
        
        return super().destroy(request, *args, **kwargs)


@login_required(login_url='/accounts/login/')
def categories_management_view(request):
    """View para renderizar a página de gerenciamento de categorias"""
    return render(request, 'categories_management/categories_management.html')