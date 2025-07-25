"""
Admin configuration for admin dashboard app.
"""

from django.contrib import admin
from .models import SystemSettings, AdminNotification, AuditLog


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'is_active', 'updated_by', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'priority', 'is_read', 'created_at')
    list_filter = ('priority', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__email')
    readonly_fields = ('created_at', 'read_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_repr', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__email', 'model_name', 'object_repr')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
