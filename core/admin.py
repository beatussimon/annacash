"""
Admin configuration for core app.
"""
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericInlineModelAdmin

from .models import WakalaRole, MchezoRole, AuditLog


@admin.register(WakalaRole)
class WakalaRoleAdmin(admin.ModelAdmin):
    list_display = ('wakala', 'user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'wakala')
    search_fields = ('user__email', 'user__first_name', 'wakala__name')
    raw_id_fields = ('user', 'wakala', 'granted_by')


@admin.register(MchezoRole)
class MchezoRoleAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'group')
    search_fields = ('user__email', 'user__first_name', 'group__name')
    raw_id_fields = ('user', 'group', 'granted_by')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'content_type', 
                   'object_id', 'description')
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('user__email', 'description')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'user', 'action', 'content_type', 
                      'object_id', 'ip_address', 'user_agent', 'description',
                      'old_values', 'new_values', 'metadata')
    
    def has_add_permission(self, request):
        """Audit logs should not be manually added."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs should not be manually changed."""
        return False
