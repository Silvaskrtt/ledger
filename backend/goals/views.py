# backend/goals/views.py

from rest_framework import generics
from .models import FinancialGoal
from .serializers import FinancialGoalSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

class FinancialGoalListCreateView(generics.ListCreateAPIView):
    serializer_class = FinancialGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FinancialGoal.objects.filter(id_user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(id_user=self.request.user)                

class FinancialGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FinancialGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FinancialGoal.objects.filter(id_user=self.request.user)

    def perform_update(self, serializer):
        if self.get_object().is_cancelled:
            raise ValidationError("Meta cancelada não pode ser alterada.")
        serializer.save()
