from django.contrib import admin

# Import models to be registered
from .models import users, categories, payment_methods, accounts, installment_plans, transactions, budgets, financial_goals, tags, recurrence_rules, transaction_tags, transaction_accounts, budget_categories_limits
class infrastructureAdmin(admin.ModelAdmin):
    ...  
# Register models for admin interface
admin.site.register(users, infrastructureAdmin)
admin.site.register(categories, infrastructureAdmin)
admin.site.register(payment_methods, infrastructureAdmin)
admin.site.register(accounts, infrastructureAdmin)
admin.site.register(installment_plans, infrastructureAdmin)
admin.site.register(transactions, infrastructureAdmin)
admin.site.register(budgets, infrastructureAdmin)
admin.site.register(financial_goals, infrastructureAdmin)
admin.site.register(tags, infrastructureAdmin)
admin.site.register(recurrence_rules, infrastructureAdmin)
admin.site.register(transaction_tags, infrastructureAdmin)
admin.site.register(transaction_accounts, infrastructureAdmin)
admin.site.register(budget_categories_limits, infrastructureAdmin)