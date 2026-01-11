# backend/categories/models.py

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
        default='#3B82F6',  # Cor padrão azul
        help_text="Cor em formato hexadecimal (#RRGGBB)"
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='categories',
        db_column='id_user'
    )
    
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,  # Alterado de CASCADE para SET_NULL
        null=True,
        blank=True,
        related_name='subcategories',
        db_column='id_parent_category'
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
        ordering = ['type', 'name']  # Ordena por tipo e depois por nome

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def is_expense(self):
        """Verifica se é uma categoria de despesa"""
        return self.type == 'OUT'
    
    def is_income(self):
        """Verifica se é uma categoria de renda"""
        return self.type == 'IN'
    
    def get_subcategories(self):
        """Retorna todas as subcategorias desta categoria"""
        return self.subcategories.all()