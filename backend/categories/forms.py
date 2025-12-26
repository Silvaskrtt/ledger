"""Formulários para gerenciamento de categorias."""

from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'id_parent_category']