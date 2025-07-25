"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import User, UserProfile, LoginHistory


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role-based functionality."""
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'created_at', 'email_verified')
    search_fields = ('email', 'first_name', 'last_name', 'department')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'department', 'profile_picture')}),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
        (_('Security'), {'fields': ('email_verified', 'failed_login_attempts', 'account_locked_until', 'last_login_ip')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'last_login_ip')
    
    actions = ['activate_users', 'deactivate_users', 'reset_failed_login_attempts']
    
    def activate_users(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def reset_failed_login_attempts(self, request, queryset):
        """Reset failed login attempts for selected users."""
        updated = queryset.update(failed_login_attempts=0, account_locked_until=None)
        self.message_user(request, f'Failed login attempts reset for {updated} users.')
    reset_failed_login_attempts.short_description = "Reset failed login attempts"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('profile')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for User Profile."""
    
    list_display = ('user_email', 'location', 'email_notifications', 'sms_notifications', 'updated_at')
    list_filter = ('email_notifications', 'sms_notifications', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'location', 'skills')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Basic Information'), {'fields': ('bio', 'location', 'website', 'linkedin_profile')}),
        (_('Volunteer Information'), {'fields': ('skills', 'interests', 'availability')}),
        (_('Notifications'), {'fields': ('email_notifications', 'sms_notifications')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin for Login History."""
    
    list_display = ('user_email', 'ip_address', 'login_time', 'logout_time', 'login_successful', 'country', 'city')
    list_filter = ('login_successful', 'login_time', 'country')
    search_fields = ('user__email', 'ip_address', 'country', 'city')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'login_time', 'logout_time', 'session_key', 'login_successful')
    date_hierarchy = 'login_time'
    
    fieldsets = (
        (_('User Information'), {'fields': ('user', 'login_successful', 'failure_reason')}),
        (_('Session Information'), {'fields': ('ip_address', 'user_agent', 'session_key')}),
        (_('Timing'), {'fields': ('login_time', 'logout_time')}),
        (_('Location'), {'fields': ('country', 'city')}),
    )
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def has_add_permission(self, request):
        """Disable adding login history records manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing login history records."""
        return False
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


# Customize admin site
admin.site.site_header = "NEXAS Administration"
admin.site.site_title = "NEXAS Admin Portal"
admin.site.index_title = "Welcome to NEXAS Administration"
