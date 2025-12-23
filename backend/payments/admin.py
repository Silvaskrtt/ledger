from django.contrib import admin
from .models import PaymentMethod, InstallmentPlan


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('id_payment_method', 'type', 'description', 'requires_account', 'allows_installments','id_user')
    search_fields = ('description',)


@admin.register(InstallmentPlan)
class InstallmentPlanAdmin(admin.ModelAdmin):
    list_display = ('id_installment_plan', 'total_amount', 'installments', 'start_date', 'id_user', 'id_account', 'id_category')
    search_fields = ('id_installment_plan',)
