from django.contrib import admin
from .models import Account

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'balance', 'created_at']
    search_fields = ['name', 'user__email']
    list_filter = ['created_at']
