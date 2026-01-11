from django.contrib import admin
from .models import PaymentMethod, InstallmentPlan


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('payment_method', 'type', 'description', 'requires_account', 'allows_installments','user')
    search_fields = ('description',)


@admin.register(InstallmentPlan)
class InstallmentPlanAdmin(admin.ModelAdmin):
    list_display = ('installment_plan', 'total_amount', 'installments', 'start_date', 'user', 'account')
    search_fields = ('installment_plan',)
