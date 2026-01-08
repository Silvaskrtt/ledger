# backend/recurrence/views.py

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import RecurrenceRule
from .serializers import RecurrenceRuleSerializer


class RecurrenceRuleListCreateView(generics.ListCreateAPIView):
    serializer_class = RecurrenceRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtra apenas recorrências do usuário atual
        return RecurrenceRule.objects.filter(id_user=self.request.user)
    
    def perform_create(self, serializer):
        # Associa automaticamente ao usuário atual
        serializer.save(id_user=self.request.user)

class RecurrenceRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RecurrenceRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtra apenas recorrências do usuário atual
        return RecurrenceRule.objects.filter(id_user=self.request.user)
