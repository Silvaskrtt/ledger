from django.contrib import admin
from .models import payment_methods, installment_plans


@admin.register(payment_methods)
class paymentMethodsAdmin(admin.ModelAdmin):
    list_display = ('id_payment_method', 'description', 'requires_account', 'allows_installments','id_user')
    search_fields = ('name', 'description',)


@admin.register(installment_plans)
class installmentPlansAdmin(admin.ModelAdmin):
    list_display = ('id_installment_plan', 'total_amount', 'installments', 'start_date', 'id_user', 'id_account', 'id_category')
    search_fields = ('id_installment_plan',)
