from django.contrib import admin
from .models import tags


@admin.register(tags)
class tagsAdmin(admin.ModelAdmin):
    list_display = ('id_tag', 'name', 'id_user')
    search_fields = ('name',)
