from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id_account', 'type', 'active', 'id_user')
    search_fields = ('id_user__email',)
