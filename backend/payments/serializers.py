# backend/payments/serializers.py

from rest_framework import serializers
from .models import PaymentMethod, InstallmentPlan


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['payment_method', 'type', 'description', 'requires_account', 'allows_installments', 'user']
        read_only_fields = ['payment_method']


class InstallmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPlan
        fields = ['installment_plan', 'user', 'account', 'category', 'total_amount', 'installments', 'start_date']
        read_only_fields = ['installment_plan']
