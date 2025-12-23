from django.contrib import admin
from .models import Transaction, TransactionAccount, TransactionTag


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'amount', 'direction', 'occurred_at', 'created_at', 'currency', 'origin', 'id_user', 'id_category', 'id_payment_method', 'id_installment_plan')
    search_fields = ('id_transaction',)


@admin.register(TransactionAccount)
class TransactionAccountAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'id_account', 'role')
    search_fields = ('id_transaction',)


@admin.register(TransactionTag)
class TransactionTagAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'id_tag')
    search_fields = ('id_transaction',)
