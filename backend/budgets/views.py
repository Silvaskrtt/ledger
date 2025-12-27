from rest_framework import generics
from .models import Budget, BudgetCategoryLimit
from .serializers import BudgetSerializer, BudgetCategoryLimitSerializer


class BudgetListCreateView(generics.ListCreateAPIView):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer


class BudgetCategoryLimitListCreateView(generics.ListCreateAPIView):
    queryset = BudgetCategoryLimit.objects.all()
    serializer_class = BudgetCategoryLimitSerializer


class BudgetCategoryLimitDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BudgetCategoryLimit.objects.all()
    serializer_class = BudgetCategoryLimitSerializer
