from django.contrib import admin
from .models import Goal

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'target', 'current', 'progress_percentage', 'deadline', 'completed', 'created_at']
    list_filter = ['completed', 'created_at', 'deadline', 'user']
    search_fields = ['title', 'description', 'user__username', 'user__email']
    readonly_fields = ['progress_percentage', 'remaining_amount', 'days_remaining', 'deadline_status']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'title', 'description', 'icon')
        }),
        ('Valores', {
            'fields': ('target', 'current', 'completed')
        }),
        ('Prazos', {
            'fields': ('deadline', 'created_at', 'updated_at')
        }),
        ('Propriedades Calculadas', {
            'fields': ('progress_percentage', 'remaining_amount', 'days_remaining', 'deadline_status'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)