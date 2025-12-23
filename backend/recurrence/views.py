from rest_framework import viewsets
from .models import RecurrenceRule
from .serializers import RecurrenceRuleSerializer


class RecurrenceRuleViewSet(viewsets.ModelViewSet):
    queryset = RecurrenceRule.objects.all()
    serializer_class = RecurrenceRuleSerializer
