"""Views para gerenciamento de categorias."""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .forms import CategoryForm
from rest_framework import viewsets
from .models import Category
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
class CategoryCreateView(View):
    """View para criar uma nova categoria."""
    template_name = 'categories/category_form.html'

    def get(self, request):
        form = CategoryForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
        return render(request, self.template_name, {'form': form})

""""class CategoryListView(View):
View para listar categorias.
    template_name = 'categories/category_list.html'

    def get(self, request):
        categories = Category.objects.all()
        return render(request, self.template_name, {'categories': categories})"""