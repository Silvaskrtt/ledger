from rest_framework import generics
from .models import RecurrenceRule
from .serializers import RecurrenceRuleSerializer


class RecurrenceRuleListCreateView(generics.ListCreateAPIView):
    queryset = RecurrenceRule.objects.all()
    serializer_class = RecurrenceRuleSerializer


class RecurrenceRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RecurrenceRule.objects.all()
    serializer_class = RecurrenceRuleSerializer
