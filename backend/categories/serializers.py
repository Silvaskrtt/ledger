from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id_category', 'name', 'id_user', 'id_parent_category']
        read_only_fields = ['id_category']
