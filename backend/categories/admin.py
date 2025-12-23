from django.contrib import admin
from .models import categories


@admin.register(categories)
class categoriesAdmin(admin.ModelAdmin):
    list_display = ('id_category', 'name', 'id_parent_category', 'id_user')
    search_fields = ('name',)
