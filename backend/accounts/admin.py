from django.contrib import admin
from .models import accounts


@admin.register(accounts)
class accountsAdmin(admin.ModelAdmin):
    list_display = ('id_account', 'type', 'active', 'id_user')
    search_fields = ('name',)
