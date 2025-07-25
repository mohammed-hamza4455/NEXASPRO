"""
URL patterns for admin dashboard.
"""

from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('settings/', views.system_settings, name='settings'),
    path('analytics/', views.user_analytics, name='analytics'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('api/stats/', views.dashboard_api_stats, name='api_stats'),
]
