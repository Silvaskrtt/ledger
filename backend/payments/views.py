from rest_framework import generics
from .models import PaymentMethod, InstallmentPlan
from .serializers import PaymentMethodSerializer, InstallmentPlanSerializer


class PaymentMethodListCreateView(generics.ListCreateAPIView):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer


class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer


class InstallmentPlanListCreateView(generics.ListCreateAPIView):
    queryset = InstallmentPlan.objects.all()
    serializer_class = InstallmentPlanSerializer


class InstallmentPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InstallmentPlan.objects.all()
    serializer_class = InstallmentPlanSerializer
