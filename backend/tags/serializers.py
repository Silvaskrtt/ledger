# backend/tags/serializers.py

from rest_framework import serializers
from .models import Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['tag', 'name', 'color', 'user', 'created_at', 'updated_at']
        read_only_fields = ['tag', 'created_at', 'updated_at', 'user']
    
    def validate(self, data):
        # Remover a validação problemática
        return data
    
    def create(self, validated_data):
        # Garantir que o usuário seja o atual
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)