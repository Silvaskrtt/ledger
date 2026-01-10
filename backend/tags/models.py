# backend/tags/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User


class Tag(models.Model):
    id_tag = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(max_length=100)
    
    color = models.CharField(
        max_length=7,
        default='#6B7280',  # Cor padrão cinza
        help_text="Cor em formato hexadecimal (#RRGGBB)"
    )
    
    id_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tags'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'name'],
                name='unique_tag_per_user'
            )
        ]
        ordering = ['name']  # Ordenação padrão

    def __str__(self):
        return self.name