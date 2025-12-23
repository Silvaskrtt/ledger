import uuid
from django.db import models
from django.contrib.auth.models import User
from users.models import users


class tags(models.Model):
    id_tag = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100)
    
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='tags')
    
    # Unique constraint to ensure tag names are unique per user
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'name'],
                name='unique_tag_per_user'
            )
        ]