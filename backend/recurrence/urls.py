from django.urls import path
from .views import RecurrenceRuleListCreateView, RecurrenceRuleDetailView

urlpatterns = [
    path('recurrence-rules/', RecurrenceRuleListCreateView.as_view(), name='recurrence-rule-list'),
    path('recurrence-rules/<int:pk>/', RecurrenceRuleDetailView.as_view(), name='recurrence-rule-detail'),
]
