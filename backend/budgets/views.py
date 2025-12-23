from rest_framework import viewsets
from .models import Budget, BudgetCategoryLimit
from .serializers import BudgetSerializer, BudgetCategoryLimitSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer


class BudgetCategoryLimitViewSet(viewsets.ModelViewSet):
    queryset = BudgetCategoryLimit.objects.all()
    serializer_class = BudgetCategoryLimitSerializer
