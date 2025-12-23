from rest_framework import viewsets
from .models import PaymentMethod, InstallmentPlan
from .serializers import PaymentMethodSerializer, InstallmentPlanSerializer


class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer


class InstallmentPlanViewSet(viewsets.ModelViewSet):
    queryset = InstallmentPlan.objects.all()
    serializer_class = InstallmentPlanSerializer
