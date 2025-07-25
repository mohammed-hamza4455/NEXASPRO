"""
Admin configuration for volunteer dashboard models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    VolunteerTask, VolunteerActivity, VolunteerReport, 
    VolunteerSkill, VolunteerAvailability, VolunteerEvent,
    VolunteerEventRegistration, VolunteerResource, VolunteerResourceAccess
)


@admin.register(VolunteerTask)
class VolunteerTaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'assigned_to', 'assigned_by', 'priority', 
        'status', 'due_date', 'completion_status', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'assigned_by', 'created_at', 
        'due_date', 'completion_date'
    ]
    search_fields = [
        'title', 'description', 'assigned_to__email', 
        'assigned_to__first_name', 'assigned_to__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'is_overdue']
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_by')
        }),
        ('Timeline', {
            'fields': ('due_date', 'start_date', 'completion_date')
        }),
        ('Hours Tracking', {
            'fields': ('estimated_hours', 'actual_hours')
        }),
        ('Additional Information', {
            'fields': ('notes', 'attachments')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_overdue'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    
    def completion_status(self, obj):
        """Display completion status with color coding."""
        if obj.status == 'completed':
            return format_html(
                '<span style="color: green;">✓ Completed</span>'
            )
        elif obj.is_overdue:
            return format_html(
                '<span style="color: red;">⚠ Overdue</span>'
            )
        elif obj.status == 'in_progress':
            return format_html(
                '<span style="color: orange;">⚡ In Progress</span>'
            )
        else:
            return format_html(
                '<span style="color: gray;">⏳ Pending</span>'
            )
    completion_status.short_description = 'Completion Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'assigned_to', 'assigned_by'
        )


@admin.register(VolunteerActivity)
class VolunteerActivityAdmin(admin.ModelAdmin):
    list_display = [
        'volunteer', 'activity_type', 'title', 'hours_logged', 
        'activity_date', 'task_link'
    ]
    list_filter = [
        'activity_type', 'activity_date', 'volunteer', 'task'
    ]
    search_fields = [
        'title', 'description', 'volunteer__email', 
        'volunteer__first_name', 'volunteer__last_name'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'activity_date'
    
    def task_link(self, obj):
        """Display link to related task if exists."""
        if obj.task:
            url = reverse('admin:volunteer_dashboard_volunteertask_change', args=[obj.task.id])
            return format_html('<a href="{}">{}</a>', url, obj.task.title)
        return '-'
    task_link.short_description = 'Related Task'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'volunteer', 'task'
        )


@admin.register(VolunteerReport)
class VolunteerReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'volunteer', 'report_type', 'status', 
        'submitted_at', 'reviewed_by', 'hours_worked'
    ]
    list_filter = [
        'report_type', 'status', 'submitted_at', 'reviewed_at',
        'volunteer', 'reviewed_by'
    ]
    search_fields = [
        'title', 'description', 'content', 'volunteer__email',
        'volunteer__first_name', 'volunteer__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'submitted_at']
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'description', 'report_type', 'status')
        }),
        ('Content', {
            'fields': ('content', 'achievements', 'challenges', 'suggestions')
        }),
        ('Assignment & Timeline', {
            'fields': ('volunteer', 'task', 'period_start', 'period_end')
        }),
        ('Hours & Work Details', {
            'fields': ('hours_worked', 'attachments')
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_comments')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'submitted_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'volunteer', 'task', 'reviewed_by'
        )


@admin.register(VolunteerSkill)
class VolunteerSkillAdmin(admin.ModelAdmin):
    list_display = [
        'volunteer', 'skill_name', 'category', 'proficiency_display',
        'years_experience', 'verified', 'verified_by'
    ]
    list_filter = [
        'category', 'proficiency_level', 'verified', 'verified_by'
    ]
    search_fields = [
        'skill_name', 'category', 'volunteer__email',
        'volunteer__first_name', 'volunteer__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    def proficiency_display(self, obj):
        """Display proficiency level with stars."""
        stars = '★' * obj.proficiency_level + '☆' * (5 - obj.proficiency_level)
        return format_html(
            '<span title="{}">{}</span>',
            obj.get_proficiency_level_display(),
            stars
        )
    proficiency_display.short_description = 'Proficiency'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'volunteer', 'verified_by'
        )


@admin.register(VolunteerAvailability)
class VolunteerAvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'volunteer', 'day_of_week_display', 'time_range',
        'max_hours_per_day', 'is_active'
    ]
    list_filter = [
        'day_of_week', 'is_active', 'volunteer'
    ]
    search_fields = [
        'volunteer__email', 'volunteer__first_name', 'volunteer__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    def day_of_week_display(self, obj):
        """Display day of week name."""
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = 'Day'
    
    def time_range(self, obj):
        """Display time range."""
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_range.short_description = 'Time Range'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('volunteer')


# Inline admin classes for related models
class VolunteerTaskInline(admin.TabularInline):
    model = VolunteerTask
    extra = 0
    fields = ['title', 'priority', 'status', 'due_date']
    readonly_fields = ['created_at']


class VolunteerActivityInline(admin.TabularInline):
    model = VolunteerActivity
    extra = 0
    fields = ['activity_type', 'title', 'hours_logged', 'activity_date']
    readonly_fields = ['created_at']


class VolunteerSkillInline(admin.TabularInline):
    model = VolunteerSkill
    extra = 0
    fields = ['skill_name', 'category', 'proficiency_level', 'verified']


class VolunteerAvailabilityInline(admin.TabularInline):
    model = VolunteerAvailability
    extra = 0
    fields = ['day_of_week', 'start_time', 'end_time', 'is_active']


@admin.register(VolunteerEvent)
class VolunteerEventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'event_type', 'status', 'start_date', 'location',
        'registration_count', 'volunteers_needed', 'organizer'
    ]
    list_filter = [
        'event_type', 'status', 'start_date', 'end_date', 'organizer'
    ]
    search_fields = [
        'title', 'description', 'location', 'organizer__email',
        'organizer__first_name', 'organizer__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'registration_count']
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'event_type', 'status')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'location', 'location_details')
        }),
        ('Volunteers', {
            'fields': ('volunteers_needed', 'max_volunteers', 'registration_deadline')
        }),
        ('Organization', {
            'fields': ('organizer', 'requirements', 'equipment_provided')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_phone', 'contact_email')
        }),
        ('Additional Settings', {
            'fields': ('is_featured', 'estimated_hours', 'image', 'attachments')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'registration_count'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'start_date'
    
    def registration_count(self, obj):
        """Display current registration count."""
        count = obj.registration_count
        max_vol = obj.max_volunteers
        if max_vol:
            return f"{count}/{max_vol}"
        return str(count)
    registration_count.short_description = 'Registrations'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organizer')


@admin.register(VolunteerEventRegistration)
class VolunteerEventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'volunteer', 'event', 'attendance_status', 'registration_date',
        'hours_contributed', 'confirmation_date'
    ]
    list_filter = [
        'attendance_status', 'registration_date', 'confirmation_date',
        'event__event_type', 'event__status'
    ]
    search_fields = [
        'volunteer__email', 'volunteer__first_name', 'volunteer__last_name',
        'event__title', 'event__location'
    ]
    readonly_fields = ['registration_date']
    fieldsets = (
        ('Registration Information', {
            'fields': ('volunteer', 'event', 'attendance_status')
        }),
        ('Dates', {
            'fields': ('registration_date', 'confirmation_date')
        }),
        ('Event Participation', {
            'fields': ('hours_contributed', 'feedback', 'notes')
        }),
        ('Emergency & Special Requirements', {
            'fields': ('emergency_contact', 'emergency_phone', 'dietary_restrictions', 'special_requirements')
        }),
    )
    date_hierarchy = 'registration_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('volunteer', 'event')


@admin.register(VolunteerResource)
class VolunteerResourceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'resource_type', 'access_level', 'download_count',
        'is_featured', 'is_active', 'last_updated'
    ]
    list_filter = [
        'resource_type', 'access_level', 'is_featured', 'is_active',
        'last_updated', 'created_by'
    ]
    search_fields = [
        'title', 'description', 'category', 'tags', 'author'
    ]
    readonly_fields = ['created_at', 'download_count']
    fieldsets = (
        ('Resource Information', {
            'fields': ('title', 'description', 'resource_type', 'access_level')
        }),
        ('File Details', {
            'fields': ('file_url', 'file_size', 'version')
        }),
        ('Organization', {
            'fields': ('category', 'tags', 'author', 'created_by')
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_active', 'last_updated')
        }),
        ('Metadata', {
            'fields': ('created_at', 'download_count'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'last_updated'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(VolunteerResourceAccess)
class VolunteerResourceAccessAdmin(admin.ModelAdmin):
    list_display = [
        'volunteer', 'resource', 'access_type', 'access_date', 'ip_address'
    ]
    list_filter = [
        'access_type', 'access_date', 'resource__resource_type'
    ]
    search_fields = [
        'volunteer__email', 'volunteer__first_name', 'volunteer__last_name',
        'resource__title', 'ip_address'
    ]
    readonly_fields = ['access_date', 'ip_address', 'user_agent']
    date_hierarchy = 'access_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('volunteer', 'resource')
