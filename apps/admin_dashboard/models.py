"""
Models for admin dashboard functionality.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SystemSettings(models.Model):
    """
    System-wide settings that can be configured by admins.
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = _('System Setting')
        verbose_name_plural = _('System Settings')
        ordering = ['key']

    def __str__(self):
        return self.key


class AdminNotification(models.Model):
    """
    Notifications for admin users.
    """
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Admin Notification')
        verbose_name_plural = _('Admin Notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient.email}"


class AuditLog(models.Model):
    """
    Audit log for tracking admin actions.
    """
    ACTION_CHOICES = [
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('view', _('View')),
        ('export', _('Export')),
        ('import', _('Import')),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} {self.model_name} at {self.timestamp}"
