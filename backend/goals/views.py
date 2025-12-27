from rest_framework import generics
from .models import FinancialGoal
from .serializers import FinancialGoalSerializer


class FinancialGoalListCreateView(generics.ListCreateAPIView):
    queryset = FinancialGoal.objects.all()
    serializer_class = FinancialGoalSerializer


class FinancialGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FinancialGoal.objects.all()
    serializer_class = FinancialGoalSerializer
