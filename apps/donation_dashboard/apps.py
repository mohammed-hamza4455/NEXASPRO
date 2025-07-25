"""
Django app configuration for donation dashboard.
"""

from django.apps import AppConfig


class DonationDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.donation_dashboard'
    verbose_name = 'Donation Dashboard'
