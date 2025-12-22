from django.contrib import admin

# Import models to be registered
from .models import users, categories, payment_methods, accounts, installment_plans, transactions, budgets, financial_goals, tags, recurrence_rules, transaction_tags, transaction_accounts, budget_categories_limits

# Define admin classes for models
class userInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_user', 'name', 'surname', 'email')
    search_fields = ('username', 'email')
    
class categoriesInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_category', 'name', 'id_parent_category', 'id_user')
    search_fields = ('name',)

class paymentMethodsInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_payment_method', 'description', 'requires_account', 'allows_installments','id_user')
    search_fields = ('name',)
    
class accountsInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_account', 'type', 'active', 'id_user')
    search_fields = ('name',)

class installmentPlansInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_installment_plan', 'total_amount', 'installments', 'start_date', 'id_user', 'id_account', 'id_category')
    search_fields = ('id_installment_plan',)

class transactionsInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'amount', 'direction', 'occurred_at', 'created_at', 'currency', 'origin', 'id_user', 'id_category', 'id_payment_method', 'id_installment_plan')
    search_fields = ('id_transaction',)

class budgetInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_budget', 'period_type', 'period_start', 'id_user')
    search_fields = ('id_budget',)

class financialGoalsInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_financial_goal', 'target_amount', 'deadline', 'strategy', 'status', 'id_user')
    search_fields = ('name',)
    
class tagsInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_tag', 'name', 'id_user')
    search_fields = ('name',)

class recurrenceRulesInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_recurrence_rule', 'frequency', 'next_execution', 'max_executions', 'executions_count', 'amount', 'direction', 'id_user', 'id_category', 'id_payment_method', 'id_account')
    search_fields = ('id_recurrence_rule',)
    
class trasactionTagsInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'id_tag')
    search_fields = ('id_transaction',)
    
class transactionAccountsInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_transaction', 'id_account', 'role')
    search_fields = ('id_transaction',)

class budgetCategoryLimitsInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('id_budget', 'limit_amount', 'id_budget', 'id_category')
    search_fields = ('id_budget_category_limit',)

# Register models for admin interface
admin.site.register(users, userInfrastructureAdmin)
admin.site.register(categories, categoriesInfrastructureAdmin)
admin.site.register(payment_methods, paymentMethodsInfrastructureAdmin)
admin.site.register(accounts, accountsInfrastructureAdmin)
admin.site.register(installment_plans, installmentPlansInfrastructureAdmin)
admin.site.register(transactions, transactionsInfrastructureAdmin)
admin.site.register(budgets, budgetInfrastructureAdmin)
admin.site.register(financial_goals, financialGoalsInfrastructureAdmin)
admin.site.register(tags, tagsInfrastructureAdmin)
admin.site.register(recurrence_rules, recurrenceRulesInfrastructureAdmin)
admin.site.register(transaction_tags, trasactionTagsInfrastructureAdmin)
admin.site.register(transaction_accounts, transactionAccountsInfrastructureAdmin)
admin.site.register(budget_categories_limits, budgetCategoryLimitsInfrastructureAdmin)