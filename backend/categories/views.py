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
        return Category.objects.filter(id_user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(id_user=self.request.user)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(id_user=self.request.user)
    
def categories_management_view(request):
    return render(request, 'categories_management/categories_management.html')