from rest_framework import viewsets
from .models import FinancialGoal
from .serializers import FinancialGoalSerializer


class FinancialGoalViewSet(viewsets.ModelViewSet):
    queryset = FinancialGoal.objects.all()
    serializer_class = FinancialGoalSerializer
