# backend/tags/serializers.py

from rest_framework import serializers
from .models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id_tag', 'name', 'color', 'id_user', 'created_at', 'updated_at']
        read_only_fields = ['id_tag', 'created_at', 'updated_at', 'id_user']
    
    def validate(self, data):
        if self.context['request'].user != data.get('id_user', self.context['request'].user):
            raise serializers.ValidationError("Você só pode criar tags para seu próprio usuário.")
        return data