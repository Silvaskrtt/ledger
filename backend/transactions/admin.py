from django.contrib import admin
from .models import Transaction, TransactionAccount, TransactionTag


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'amount', 'direction', 'occurred_at', 'created_at', 'currency', 'origin', 'user', 'category', 'payment_method', 'installment_plan')
    search_fields = ('transaction',)


@admin.register(TransactionAccount)
class TransactionAccountAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'account', 'role')
    search_fields = ('transaction',)


@admin.register(TransactionTag)
class TransactionTagAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'tag')
    search_fields = ('transaction',)
