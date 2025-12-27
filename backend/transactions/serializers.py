from rest_framework import serializers
from .models import Transaction, TransactionAccount, TransactionTag


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id_transaction', 'id_user', 'id_category', 'id_payment_method', 'amount', 'direction', 'currency', 'occurred_at', 'created_at', 'origin']
        read_only_fields = ['id_transaction', 'created_at']


class TransactionAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionAccount
        fields = ['id_transaction', 'id_account']


class TransactionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionTag
        fields = ['id_transaction', 'id_tag']
