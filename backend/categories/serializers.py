# backend/categories/serializers.py

from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    subcategories_count = serializers.IntegerField(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id_category', 'name', 'type', 'type_display', 'icon', 'color',
            'id_parent_category', 'id_user', 'created_at', 'updated_at',
            'subcategories_count'
        ]
        read_only_fields = ['id_category', 'created_at', 'updated_at', 'id_user']
    
    def validate(self, data):
        # Valida se o usuário está tentando criar uma categoria para si mesmo
        if self.context['request'].user != data.get('id_user', self.context['request'].user):
            raise serializers.ValidationError("Você só pode criar categorias para seu próprio usuário.")
        return data