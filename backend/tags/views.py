# backend/tags/views.py

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, status
from .models import Tag
from .serializers import TagSerializer

class TagListCreateView(generics.ListCreateAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Tag.objects.filter(id_user=self.request.user).order_by('name')
    
    def perform_create(self, serializer):
        serializer.save(id_user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e), 'detail': 'Erro ao carregar tags'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Tag.objects.filter(id_user=self.request.user)