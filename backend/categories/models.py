import uuid
from django.db import models

from users.models import users

class categories(models.Model):
    id_category = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False)
    name = models.CharField(max_length=100, unique=True)
    
    id_user = models.ForeignKey(
        users, 
        on_delete=models.CASCADE, 
        related_name='categories')
    
    id_parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'name'],
                name='unique_category_per_user'
            )
        ]