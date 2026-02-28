from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from core.models import WakalaRole, MchezoRole


class WakalaRoleInline(admin.TabularInline):
    model = WakalaRole
    fk_name = "user"
    extra = 0
    verbose_name = "Wakala Role"
    verbose_name_plural = "Wakala Roles"
    autocomplete_fields = ["wakala"]


class MchezoRoleInline(admin.TabularInline):
    model = MchezoRole
    fk_name = "user"
    extra = 0
    verbose_name = "Mchezo Role"
    verbose_name_plural = "Mchezo Roles"
    autocomplete_fields = ["group"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Powerful custom admin for the User model.
    """

    # Display fields
    list_display = (
        "email",
        "phone_number",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("first_name", "last_name", "email", "phone_number")
    ordering = ("-date_joined",)

    # Use custom fieldsets instead of inheriting from BaseUserAdmin
    # because BaseUserAdmin expects a 'username' field which we don't have
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone_number", "bio", "profile_image")}),
        ("Location & Identity", {"fields": ("national_id", "region", "district", "timezone")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    
    # Custom add_fieldsets since we don't have username
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password"),
        }),
    )
    
    readonly_fields = ("date_joined", "last_login")

    # Inlines for roles
    inlines = [WakalaRoleInline, MchezoRoleInline]
