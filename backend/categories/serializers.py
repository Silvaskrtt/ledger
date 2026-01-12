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
        """Validações do modelo de categoria"""
        # Validar para evitar ciclos (A -> B -> A)
        if 'parent_category' in data and data['parent_category']:
            parent = data['parent_category']
            user = self.context.get('request').user
            
            # Verificar se a categoria pai pertence ao mesmo usuário
            if parent.user != user:
                raise serializers.ValidationError({
                    'parent_category': 'Categoria pai deve pertencer ao mesmo usuário.'
                })
            
            # Verificar ciclos: se self.instance existe (update), verificar se parent não é descendente de self
            if self.instance and self.instance.pk == parent.pk:
                raise serializers.ValidationError({
                    'parent_category': 'Uma categoria não pode ser sua própria categoria pai.'
                })
            
            # Verificar subcategorias para evitar ciclos
            def has_ancestor(category, ancestor_id):
                """Recursivamente verifica se ancestor_id é ancestro de category"""
                if category.parent_category is None:
                    return False
                if category.parent_category.pk == ancestor_id:
                    return True
                return has_ancestor(category.parent_category, ancestor_id)
            
            if self.instance and has_ancestor(parent, self.instance.pk):
                raise serializers.ValidationError({
                    'parent_category': 'Não é permitido criar ciclos entre categorias.'
                })
        
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