# backend/categories/serializers.py

from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    subcategories_count = serializers.IntegerField(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'category', 'name', 'type', 'type_display', 'icon', 'color',
            'parent_category', 'user', 'created_at', 'updated_at',
            'subcategories_count'
        ]
        read_only_fields = ['category', 'created_at', 'updated_at', 'user']
    
    def validate(self, data):
        # Remover validação problemática
        return data
    
    def validate_icon(self, value):
        """Permite ícone vazio, usa padrão se não especificado"""
        if not value:
            return 'receipt'
        return value
    
    def create(self, validated_data):
        # Garantir que o usuário seja o atual
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)