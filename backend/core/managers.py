from django.db import models
from django.utils import timezone


class TimestampedManager(models.Manager):
    """Custom manager for timestamped models"""
    
    def active(self):
        """Return only active records (if model has 'active' field)"""
        if hasattr(self.model, 'active'):
            return self.filter(active=True)
        return self.all()


class SoftDeleteManager(models.Manager):
    """Custom manager for soft-deleted models"""
    
    def active(self):
        """Return only non-deleted records"""
        if hasattr(self.model, 'deleted_at'):
            return self.filter(deleted_at__isnull=True)
        return self.all()
