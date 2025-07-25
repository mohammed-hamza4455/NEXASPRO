"""
URL configuration for volunteer dashboard.
"""

from django.urls import path
from . import views

app_name = 'volunteer_dashboard'

urlpatterns = [
    # Dashboard
    path('', views.volunteer_dashboard_new, name='dashboard'),
    path('old/', views.volunteer_dashboard, name='dashboard_old'),
    path('class-based/', views.VolunteerDashboardView.as_view(), name='dashboard_class'),
    
    # Tasks
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    
    # Events
    path('events/', views.events_list, name='events_list'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('my-events/', views.my_events, name='my_events'),
    
    # Resources
    path('resources/', views.resources_list, name='resources_list'),
    path('resources/<int:resource_id>/download/', views.resource_download, name='resource_download'),
    
    # Reports
    path('reports/', views.report_list, name='report_list'),
    path('reports/submit/', views.submit_report, name='submit_report'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('reports/dashboard/', views.reports_dashboard, name='reports_dashboard'),
    
    # Profile
    path('profile/', views.profile_update, name='profile_update'),
    
    # Activity
    path('activity/', views.activity_log, name='activity_log'),
    path('log-hours/', views.log_hours, name='log_hours'),
    
    # API endpoints
    path('api/stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/tasks/<int:task_id>/update-status/', views.update_task_status, name='update_task_status'),
    path('api/tasks/request/', views.request_task, name='request_task'),
    path('api/events/<int:event_id>/register/', views.register_for_event, name='register_for_event'),
    path('api/skills/add/', views.add_skill, name='add_skill'),
    path('api/availability/save/', views.save_availability, name='save_availability'),
]
