from django.contrib import admin
from .models import users


@admin.register(users)
class userAdmin(admin.ModelAdmin):
    list_display = ('id_user', 'name', 'surname', 'email')
    search_fields = ('username', 'email')
