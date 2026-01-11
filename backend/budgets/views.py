# backend/budgets/views.py

from django.contrib.auth.decorators import login_required
from rest_framework import generics
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Budget, BudgetCategoryLimit
from categories.models import Category
from transactions.models import Transaction
from django.db.models import Sum
from .serializers import BudgetSerializer, BudgetCategoryLimitSerializer
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


@login_required
def budget_view(request):
    return render(request, 'budget/budget.html', {
        'categories': Category.objects.filter(user=request.user)
    })

class BudgetOverviewAPIView(generics.ListAPIView):
    serializer_class = BudgetCategoryLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BudgetCategoryLimit.objects.filter(
            id_budget__user=self.request.user
        ).select_related('category')

    def list(self, request, *args, **kwargs):
        data = []

        for limit in self.get_queryset():
            spent = Transaction.objects.filter(
                user=request.user,
                category=limit.category,
                direction='OUT'
            ).aggregate(total=Sum('amount'))['total'] or 0

            percent = min((spent / limit.limit_amount) * 100, 100)

            data.append({
                'id': limit.id,
                'category': limit.category.name,
                'limit_amount': limit.limit_amount,
                'spent': spent,
                'remaining': limit.limit_amount - spent,
                'percent': round(percent, 1)
            })

        return Response(data)

class BudgetListCreateView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

class BudgetCategoryLimitListCreateView(generics.ListCreateAPIView):
    serializer_class = BudgetCategoryLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BudgetCategoryLimit.objects.filter(
            id_budget__user=self.request.user
        )

    def get_serializer_context(self):
        return {'request': self.request}

class BudgetCategoryLimitDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetCategoryLimitSerializer

    def get_queryset(self):
        return BudgetCategoryLimit.objects.filter(
            id_budget__user=self.request.user
        )
