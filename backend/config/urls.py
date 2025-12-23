"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from accounts.views import AccountViewSet
from transactions.views import TransactionViewSet, TransactionAccountViewSet, TransactionTagViewSet
from categories.views import CategoryViewSet
from budgets.views import BudgetViewSet, BudgetCategoryLimitViewSet
from payments.views import PaymentMethodViewSet, InstallmentPlanViewSet
from tags.views import TagViewSet
from recurrence.views import RecurrenceRuleViewSet
from goals.views import FinancialGoalViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'transaction-accounts', TransactionAccountViewSet)
router.register(r'transaction-tags', TransactionTagViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'budget-category-limits', BudgetCategoryLimitViewSet)
router.register(r'payment-methods', PaymentMethodViewSet)
router.register(r'installment-plans', InstallmentPlanViewSet)
router.register(r'tags', TagViewSet)
router.register(r'recurrence-rules', RecurrenceRuleViewSet)
router.register(r'financial-goals', FinancialGoalViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
