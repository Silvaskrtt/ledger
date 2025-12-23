from django.contrib import admin
from .models import transactions, transaction_accounts, transaction_tags


@admin.register(transactions)
class transactionsAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'amount', 'direction', 'occurred_at', 'created_at', 'currency', 'origin', 'id_user', 'id_category', 'id_payment_method', 'id_installment_plan')
    search_fields = ('id_transaction',)


@admin.register(transaction_accounts)
class transactionAccountsAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'id_account', 'role')
    search_fields = ('id_transaction',)


@admin.register(transaction_tags)
class transactionTagsAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'id_tag')
    search_fields = ('id_transaction',)
