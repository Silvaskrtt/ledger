import uuid
from django.db import models
from users.models import User


class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('CHECKING', 'Checking Account'),
        ('WALLET', 'Digital Wallet'),
        ('CREDIT_CARD', 'Credit Card'),
    ]
    
    id_account = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    active = models.BooleanField(default=True)
    id_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='accounts')
    
    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'type'],
                name='unique_account_per_user'
            )
        ]

    def __str__(self):
        return f"{self.get_type_display()} - {self.id_user.email}"