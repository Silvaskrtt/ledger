from rest_framework import serializers
from .models import PaymentMethod, InstallmentPlan


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id_payment_method', 'type', 'description', 'requires_account', 'allows_installments', 'id_user']
        read_only_fields = ['id_payment_method']


class InstallmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPlan
        fields = ['id_installment_plan', 'id_user', 'id_account', 'id_category', 'total_amount', 'installments', 'start_date']
        read_only_fields = ['id_installment_plan']
