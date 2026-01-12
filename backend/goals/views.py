# backend/goals/views.py

from rest_framework import generics
from .models import FinancialGoal
from .serializers import FinancialGoalSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import now

@login_required
def goals_page(request):
    """Página principal de metas financeiras"""
    return render(request, 'financial_goals/goals.html')

class FinancialGoalListCreateView(generics.ListCreateAPIView):
    serializer_class = FinancialGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FinancialGoal.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        # Sobrescrever para garantir que retorna um array
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)           

class FinancialGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FinancialGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FinancialGoal.objects.filter(
            user=self.request.user,
            is_deleted=False
        )

    def perform_update(self, serializer):
        if self.get_object().is_cancelled:
            raise ValidationError("Meta cancelada não pode ser alterada.")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.deleted_at = now()
        instance.save()