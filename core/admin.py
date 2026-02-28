from django.contrib import admin
from .models import AuditLog, WakalaRole, MchezoRole


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Powerful admin for viewing the system audit trail.
    This is a read-only log.
    """

    list_display = ("timestamp", "user", "action", "target", "description")
    list_filter = ("action", "timestamp", "user")
    search_fields = ("user__email", "description", "old_values", "new_values")
    readonly_fields = [
        f.name for f in AuditLog._meta.fields
    ]  # Make all fields read-only
    ordering = ("-timestamp",)

    def target(self, obj):
        """Display a link to the related object, if it exists."""
        if obj.content_object:
            return str(obj.content_object)
        return "N/A"

    target.short_description = "Target Object"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# The Role models are better managed inline from the User admin,
# but we register them here to allow for raw editing if needed.
@admin.register(WakalaRole)
class WakalaRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "wakala", "role")
    list_filter = ("role",)
    search_fields = ("user__email", "wakala__name")
    autocomplete_fields = ["user", "wakala"]


@admin.register(MchezoRole)
class MchezoRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "group", "role")
    list_filter = ("role",)
    search_fields = ("user__email", "group__name")
    autocomplete_fields = ["user", "group"]
