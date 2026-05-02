# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile


# ===============================
# Inline Profile no User
# ===============================

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Perfil"


# ===============================
# Customização do User Admin
# ===============================

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_role",
        "is_staff",
    )
    
    def get_role(self, obj):
        """Retorna a role do usuário"""
        try:
            return obj.profile.role
        except Profile.DoesNotExist:
            return "Sem perfil"
    get_role.short_description = "Perfil"
    get_role.admin_order_field = 'profile__role'


# ===============================
# Re-registrar User
# ===============================

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ===============================
# Registrar Profile
# ===============================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")
    list_editable = ("role",)  # Permite editar direto na lista