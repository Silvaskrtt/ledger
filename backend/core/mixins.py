from rest_framework import serializers


class TimestampedMixin(serializers.Serializer):
    """Mixin to add created_at and updated_at fields to serializers"""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UserFilterMixin:
    """Mixin to filter querysets by current user"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request and self.request.user.is_authenticated:
            return queryset.filter(id_user=self.request.user)
        return queryset
