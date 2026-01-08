from rest_framework.permissions import IsAuthenticated

from rest_framework import generics
from .models import Tag
from .serializers import TagSerializer


class TagListCreateView(generics.ListCreateAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Tag.objects.filter(id_user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(id_user=self.request.user)


class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Tag.objects.filter(id_user=self.request.user)
