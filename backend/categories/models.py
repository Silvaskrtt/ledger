import uuid
from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    TYPE_CHOICES = [
        ('IN', 'Entrada'),    # Income
        ('OUT', 'Saída'),     # Expense
    ]
    
    category = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        db_column='id_category'
    )
    
    name = models.CharField(max_length=100)
    
    type = models.CharField(
        max_length=3,
        choices=TYPE_CHOICES,
        default='OUT',
        help_text="Se a categoria é para entrada (renda) ou saída (despesa)"
    )
    
    icon = models.CharField(
        max_length=50,
        default='receipt',
        blank=True,
        help_text="Nome do ícone (Font Awesome, Material Icons, etc.)"
    )
    
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Cor em formato hexadecimal (#RRGGBB)"
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='categories',
        db_column='id_user_id',
        db_index=True
    )
    
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        db_column='id_parent_category_id'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_category_per_user'
            )
        ]
        ordering = ['type', 'name']

    def __str__(self):
        parent_str = f" ({self.parent_category.name})" if self.parent_category else ""
        return f"{self.name}{parent_str} ({self.get_type_display()})"
    
    def get_type_display(self):
        """Retorna o display name do tipo"""
        return dict(self.TYPE_CHOICES).get(self.type, self.type)
    
    def get_subcategories_count(self):
        """Retorna a quantidade de subcategorias"""
        return self.subcategories.count()
    
    def is_root_category(self):
        """Verifica se é uma categoria raiz (sem pai)"""
        return self.parent_category is None
    
    def get_all_descendants(self):
        """Retorna todas as categorias descendentes"""
        descendants = []
        for subcat in self.subcategories.all():
            descendants.append(subcat)
            descendants.extend(subcat.get_all_descendants())
        return descendants
    
    def can_be_parent_of(self, category):
        """Verifica se esta categoria pode ser pai de outra categoria"""
        if self == category:
            return False
        if category in self.get_all_descendants():
            return False
        return True