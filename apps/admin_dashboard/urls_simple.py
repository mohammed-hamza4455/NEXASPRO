"""
Simple URL patterns for admin dashboard.
"""

from django.urls import path
from . import views_simple

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views_simple.admin_dashboard_simple, name='dashboard'),
]
