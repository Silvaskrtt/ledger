# backend/payments/views.py

from rest_framework.permissions import IsAuthenticated

from rest_framework import generics
from .models import PaymentMethod, InstallmentPlan
from .serializers import PaymentMethodSerializer, InstallmentPlanSerializer


class PaymentMethodListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(id_user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(id_user=self.request.user)

class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(id_user=self.request.user)

class InstallmentPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = InstallmentPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return InstallmentPlan.objects.filter(id_user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(id_user=self.request.user)


class InstallmentPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InstallmentPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return InstallmentPlan.objects.filter(id_user=self.request.user)
