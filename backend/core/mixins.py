from rest_framework import serializers
from rest_framework import generics

class TimestampedMixin(serializers.Serializer):
    """Mixin to add created_at and updated_at fields to serializers"""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UserFilteredViewSet(generics.ListCreateAPIView):
    """Mixin to filter querysets by current user"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self, 'user_filter_field'):
            filter_dict = {self.user_filter_field: self.request.user}
            return queryset.filter(**filter_dict)
        return queryset
