from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id_account', 'type', 'active', 'id_user']
        read_only_fields = ['id_account']
