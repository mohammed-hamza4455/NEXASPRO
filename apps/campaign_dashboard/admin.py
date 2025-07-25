"""
Admin configuration for campaign dashboard.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from django.utils import timezone

from .models import (
    Campaign, CampaignGoal, CampaignMetrics, 
    CampaignVolunteer, CampaignUpdate, CampaignTask
)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """
    Admin interface for Campaign model.
    """
    list_display = [
        'name', 'manager', 'status', 'priority', 'start_date', 
        'end_date', 'budget', 'volunteer_count', 'is_active_display',
        'progress_display', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'is_featured', 'is_public', 
        'created_at', 'start_date', 'end_date'
    ]
    search_fields = ['name', 'description', 'manager__email', 'location']
    readonly_fields = ['created_at', 'updated_at', 'progress_display', 'days_remaining_display']
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'manager', 'status', 'priority')
        }),
        ('Dates & Timeline', {
            'fields': ('start_date', 'end_date', 'progress_display', 'days_remaining_display')
        }),
        ('Budget & Targets', {
            'fields': ('budget', 'target_volunteers', 'target_donations')
        }),
        ('Contact Information', {
            'fields': ('location', 'contact_email', 'contact_phone')
        }),
        ('Social Media', {
            'fields': ('website_url', 'facebook_url', 'twitter_url', 'instagram_url'),
            'classes': ('collapse',)
        }),
        ('Media & Settings', {
            'fields': ('featured_image', 'is_featured', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def volunteer_count(self, obj):
        """Display volunteer count for the campaign."""
        count = obj.campaign_volunteers.filter(status='active').count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    volunteer_count.short_description = 'Active Volunteers'
    
    def is_active_display(self, obj):
        """Display active status with color coding."""
        if obj.is_active:
            return format_html('<span style="color: #28a745;">✓ Active</span>')
        return format_html('<span style="color: #dc3545;">✗ Inactive</span>')
    is_active_display.short_description = 'Active Status'
    
    def progress_display(self, obj):
        """Display campaign progress as a progress bar."""
        progress = obj.progress_percentage
        color = '#28a745' if progress >= 75 else '#ffc107' if progress >= 50 else '#dc3545'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 4px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 4px; '
            'text-align: center; line-height: 20px; color: white; font-size: 12px;">{:.1f}%</div></div>',
            progress, color, progress
        )
    progress_display.short_description = 'Progress'
    
    def days_remaining_display(self, obj):
        """Display days remaining with color coding."""
        days = obj.days_remaining
        if days <= 0:
            return format_html('<span style="color: #dc3545;">Ended</span>')
        elif days <= 7:
            return format_html('<span style="color: #ff6b35;">{} days</span>', days)
        elif days <= 30:
            return format_html('<span style="color: #ffc107;">{} days</span>', days)
        else:
            return format_html('<span style="color: #28a745;">{} days</span>', days)
    days_remaining_display.short_description = 'Days Remaining'
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        queryset = super().get_queryset(request)
        return queryset.select_related('manager').prefetch_related('campaign_volunteers')


@admin.register(CampaignGoal)
class CampaignGoalAdmin(admin.ModelAdmin):
    """
    Admin interface for CampaignGoal model.
    """
    list_display = [
        'title', 'campaign', 'goal_type', 'target_value', 'current_value',
        'completion_display', 'is_active', 'deadline', 'created_at'
    ]
    list_filter = ['goal_type', 'is_active', 'created_at', 'deadline']
    search_fields = ['title', 'description', 'campaign__name']
    readonly_fields = ['created_at', 'updated_at', 'completion_display']
    
    fieldsets = (
        ('Goal Information', {
            'fields': ('campaign', 'goal_type', 'title', 'description')
        }),
        ('Target & Progress', {
            'fields': ('target_value', 'current_value', 'unit', 'completion_display')
        }),
        ('Settings', {
            'fields': ('is_active', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def completion_display(self, obj):
        """Display goal completion as a progress bar."""
        completion = obj.completion_percentage
        color = '#28a745' if completion >= 100 else '#ffc107' if completion >= 75 else '#dc3545'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 4px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 4px; '
            'text-align: center; line-height: 20px; color: white; font-size: 12px;">{:.1f}%</div></div>',
            min(100, completion), color, completion
        )
    completion_display.short_description = 'Completion'


@admin.register(CampaignMetrics)
class CampaignMetricsAdmin(admin.ModelAdmin):
    """
    Admin interface for CampaignMetrics model.
    """
    list_display = [
        'campaign', 'date', 'volunteers_registered', 'donations_amount',
        'volunteer_hours', 'events_held', 'people_reached', 'updated_at'
    ]
    list_filter = ['date', 'created_at', 'campaign__status']
    search_fields = ['campaign__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Campaign & Date', {
            'fields': ('campaign', 'date')
        }),
        ('Volunteer Metrics', {
            'fields': ('volunteers_registered', 'volunteers_active', 'volunteer_hours')
        }),
        ('Donation Metrics', {
            'fields': ('donations_count', 'donations_amount')
        }),
        ('Outreach Metrics', {
            'fields': ('events_held', 'people_reached', 'social_media_reach', 'website_visits')
        }),
        ('Engagement Metrics', {
            'fields': ('email_opens', 'email_clicks', 'social_shares', 'social_likes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        queryset = super().get_queryset(request)
        return queryset.select_related('campaign')


@admin.register(CampaignVolunteer)
class CampaignVolunteerAdmin(admin.ModelAdmin):
    """
    Admin interface for CampaignVolunteer model.
    """
    list_display = [
        'volunteer_name', 'campaign', 'volunteer_role', 'status',
        'hours_committed', 'hours_logged', 'progress_display', 'assigned_date'
    ]
    list_filter = ['status', 'volunteer_role', 'assigned_date', 'start_date']
    search_fields = ['volunteer__first_name', 'volunteer__last_name', 'volunteer__email', 'campaign__name']
    readonly_fields = ['assigned_date', 'created_at', 'updated_at', 'progress_display']
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('campaign', 'volunteer', 'assigned_by', 'status', 'volunteer_role')
        }),
        ('Timeline', {
            'fields': ('assigned_date', 'start_date', 'end_date')
        }),
        ('Hours & Progress', {
            'fields': ('hours_committed', 'hours_logged', 'progress_display')
        }),
        ('Details', {
            'fields': ('skills_required', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def volunteer_name(self, obj):
        """Display volunteer's full name."""
        return obj.volunteer.get_full_name()
    volunteer_name.short_description = 'Volunteer'
    volunteer_name.admin_order_field = 'volunteer__first_name'
    
    def progress_display(self, obj):
        """Display hour completion progress."""
        if obj.hours_committed > 0:
            progress = (float(obj.hours_logged) / float(obj.hours_committed)) * 100
            color = '#28a745' if progress >= 100 else '#ffc107' if progress >= 75 else '#dc3545'
            return format_html(
                '<div style="width: 100px; background-color: #e9ecef; border-radius: 4px;">'
                '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 4px; '
                'text-align: center; line-height: 20px; color: white; font-size: 12px;">{:.1f}%</div></div>',
                min(100, progress), color, progress
            )
        return format_html('<span style="color: #6c757d;">No commitment</span>')
    progress_display.short_description = 'Hours Progress'
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        queryset = super().get_queryset(request)
        return queryset.select_related('campaign', 'volunteer', 'assigned_by')


@admin.register(CampaignUpdate)
class CampaignUpdateAdmin(admin.ModelAdmin):
    """
    Admin interface for CampaignUpdate model.
    """
    list_display = [
        'title', 'campaign', 'update_type', 'author', 'is_published',
        'publish_date', 'views_count', 'likes_count', 'created_at'
    ]
    list_filter = ['update_type', 'is_published', 'is_public', 'notify_volunteers', 'send_email', 'created_at']
    search_fields = ['title', 'content', 'campaign__name', 'author__email']
    readonly_fields = ['created_at', 'updated_at', 'views_count', 'likes_count']
    
    fieldsets = (
        ('Update Information', {
            'fields': ('campaign', 'title', 'content', 'update_type', 'author')
        }),
        ('Publication Settings', {
            'fields': ('is_published', 'publish_date', 'is_public')
        }),
        ('Notification Settings', {
            'fields': ('notify_volunteers', 'send_email')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Engagement Stats', {
            'fields': ('views_count', 'likes_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        queryset = super().get_queryset(request)
        return queryset.select_related('campaign', 'author')


@admin.register(CampaignTask)
class CampaignTaskAdmin(admin.ModelAdmin):
    """
    Admin interface for CampaignTask model.
    """
    list_display = [
        'title', 'campaign', 'assigned_to', 'status', 'priority',
        'due_date', 'progress_percentage', 'estimated_hours', 'actual_hours',
        'is_overdue_display', 'created_at'
    ]
    list_filter = ['status', 'priority', 'due_date', 'created_at']
    search_fields = ['title', 'description', 'campaign__name', 'assigned_to__email']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'is_overdue_display']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('campaign', 'title', 'description', 'status', 'priority')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_by')
        }),
        ('Timeline', {
            'fields': ('due_date', 'estimated_hours', 'actual_hours', 'progress_percentage')
        }),
        ('Completion', {
            'fields': ('completed_at', 'is_overdue_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue_display(self, obj):
        """Display overdue status with color coding."""
        if obj.is_overdue:
            return format_html('<span style="color: #dc3545;">⚠ Overdue</span>')
        elif obj.status == 'completed':
            return format_html('<span style="color: #28a745;">✓ Completed</span>')
        elif obj.due_date and obj.due_date <= timezone.now() + timezone.timedelta(days=1):
            return format_html('<span style="color: #ffc107;">⏰ Due Soon</span>')
        return format_html('<span style="color: #6c757d;">On Track</span>')
    is_overdue_display.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        queryset = super().get_queryset(request)
        return queryset.select_related('campaign', 'assigned_to', 'assigned_by')


# Custom admin site configurations
admin.site.site_header = "NEXAS Campaign Management"
admin.site.site_title = "NEXAS Admin"
admin.site.index_title = "Campaign Dashboard Administration"
