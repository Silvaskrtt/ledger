from rest_framework import serializers
from rest_framework import generics
from django.db import models
from django.db.models import Manager, QuerySet
from django.utils import timezone

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


# Soft Delete Managers e Querysets
class SoftDeleteQuerySet(QuerySet):
    """QuerySet que suporta soft deletes"""
    
    def delete(self):
        """Soft delete: marca como deletado sem remover da BD"""
        return self.update(is_deleted=True, deleted_at=timezone.now())
    
    def hard_delete(self):
        """Delete permanente do BD"""
        return super().delete()
    
    def active(self):
        """Retorna apenas registros não deletados"""
        return self.filter(is_deleted=False)
    
    def deleted(self):
        """Retorna apenas registros deletados"""
        return self.filter(is_deleted=True)


class SoftDeleteManager(Manager):
    """Manager padrão que retorna apenas registros ativos"""
    
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)
    
    def all_with_deleted(self):
        """Retorna TODOS os registros, incluindo deletados"""
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def deleted_only(self):
        """Retorna apenas registros deletados"""
        return self.all_with_deleted().filter(is_deleted=True)


class SoftDeleteModel(models.Model):
    """Modelo abstrato com suporte a soft deletes"""
    
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = Manager()  # Para acessar TUDO (admin, reports)
    
    class Meta:
        abstract = True
    
    def delete(self, *args, **kwargs):
        """Soft delete: marca como deletado"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def hard_delete(self, *args, **kwargs):
        """Delete permanente"""
        super().delete(*args, **kwargs)
    
    def restore(self):
        """Restaura um soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
