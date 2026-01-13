from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    subcategories_count = serializers.IntegerField(source='get_subcategories_count', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'category', 'name', 'type', 'type_display', 'icon', 'color',
            'parent_category', 'user', 'created_at', 'updated_at', 'subcategories_count'
        ]
        read_only_fields = ['category', 'user', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Customiza a representação para incluir informações do parent"""
        representation = super().to_representation(instance)
        
        # Incluir informações do parent_category se existir
        if instance.parent_category:
            representation['parent_category_info'] = {
                'category': str(instance.parent_category.category),
                'name': instance.parent_category.name,
                'type': instance.parent_category.type
            }
        else:
            representation['parent_category_info'] = None
        
        return representation
    
    def validate(self, data):
        """Validações do modelo de categoria"""
        request = self.context.get('request')
        user = request.user if request else None
        
        # Em caso de criação, garantir user está presente
        if not self.instance and 'user' not in data:
            if not user:
                raise serializers.ValidationError("Usuário não especificado")
            data['user'] = user
        
        # Validar parent_category
        if 'parent_category' in data and data['parent_category']:
            parent = data['parent_category']
            
            # Verificar se parent pertence ao usuário
            if parent.user != user:
                raise serializers.ValidationError({
                    'parent_category': 'Categoria pai deve pertencer ao mesmo usuário.'
                })
            
            # Verificar ciclos (em update)
            if self.instance:
                if self.instance == parent:
                    raise serializers.ValidationError({
                        'parent_category': 'Uma categoria não pode ser sua própria categoria pai.'
                    })
                
                # Verificar se a categoria a ser definida como pai
                # é descendente da categoria atual (evitar ciclos)
                if parent in self.instance.get_all_descendants():
                    raise serializers.ValidationError({
                        'parent_category': 'Não é permitido criar ciclos entre categorias.'
                    })
        
        return data
    
    def create(self, validated_data):
        # Extrair parent_category se existir
        parent_category = validated_data.pop('parent_category', None)
        
        # Criar categoria
        category = Category.objects.create(**validated_data)
        
        # Definir parent_category após criação
        if parent_category:
            category.parent_category = parent_category
            category.save()
        
        return category