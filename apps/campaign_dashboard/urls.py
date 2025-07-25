"""
URL patterns for campaign dashboard.
"""

from django.urls import path
from . import views

app_name = 'campaign_dashboard'

urlpatterns = [
    # Main campaign manager dashboard
    path('', views.campaign_manager_dashboard, name='dashboard'),
    
    # Campaign management
    path('create/', views.create_campaign, name='create_campaign'),
    path('manage/<uuid:campaign_id>/', views.manage_campaign, name='manage_campaign'),
    path('details/<uuid:campaign_id>/', views.campaign_details, name='campaign_details'),
]
