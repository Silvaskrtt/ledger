from django.urls import path
from .views import TagListCreateView, TagDetailView

urlpatterns = [
    path('tags/', TagListCreateView.as_view(), name='tag-list'),
    path('tags/<int:pk>/', TagDetailView.as_view(), name='tag-detail'),
]
