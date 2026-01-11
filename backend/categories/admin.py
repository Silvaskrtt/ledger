from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'name', 'parent_category', 'user')
    search_fields = ('name',)
