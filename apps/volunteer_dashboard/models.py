"""
Models for volunteer dashboard functionality.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class VolunteerTask(models.Model):
    """
    Tasks assigned to volunteers.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('overdue', _('Overdue')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='volunteer_tasks',
        limit_choices_to={'role': 'volunteer'}
    )
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='assigned_tasks'
    )
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.25)]
    )
    actual_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    notes = models.TextField(blank=True)
    attachments = models.JSONField(blank=True, null=True)  # Store file paths/URLs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Volunteer Task')
        verbose_name_plural = _('Volunteer Tasks')
        ordering = ['-priority', 'due_date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.assigned_to.get_full_name()}"

    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            from django.utils import timezone
            return timezone.now() > self.due_date
        return False

    def get_status_display_class(self):
        """Get CSS class for status display."""
        status_classes = {
            'pending': 'warning',
            'in_progress': 'info',
            'completed': 'success',
            'cancelled': 'secondary',
            'overdue': 'danger',
        }
        return status_classes.get(self.status, 'secondary')


class VolunteerActivity(models.Model):
    """
    Volunteer activity tracking and logging.
    """
    ACTIVITY_TYPES = [
        ('task_started', _('Task Started')),
        ('task_completed', _('Task Completed')),
        ('report_submitted', _('Report Submitted')),
        ('training_attended', _('Training Attended')),
        ('event_participated', _('Event Participated')),
        ('meeting_attended', _('Meeting Attended')),
        ('hours_logged', _('Hours Logged')),
        ('skill_updated', _('Skill Updated')),
        ('profile_updated', _('Profile Updated')),
        ('feedback_submitted', _('Feedback Submitted')),
    ]

    volunteer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='volunteer_activities',
        limit_choices_to={'role': 'volunteer'}
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task = models.ForeignKey(
        VolunteerTask, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='activities'
    )
    hours_logged = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    location = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(blank=True, null=True)  # Additional data
    created_at = models.DateTimeField(auto_now_add=True)
    activity_date = models.DateTimeField()

    class Meta:
        verbose_name = _('Volunteer Activity')
        verbose_name_plural = _('Volunteer Activities')
        ordering = ['-activity_date', '-created_at']

    def __str__(self):
        return f"{self.volunteer.get_full_name()} - {self.get_activity_type_display()}"

    def get_activity_icon(self):
        """Get icon class for activity type."""
        activity_icons = {
            'task_started': 'bi-play-circle',
            'task_completed': 'bi-check-circle',
            'report_submitted': 'bi-file-text',
            'training_attended': 'bi-mortarboard',
            'event_participated': 'bi-calendar-event',
            'meeting_attended': 'bi-people',
            'hours_logged': 'bi-clock',
            'skill_updated': 'bi-award',
            'profile_updated': 'bi-person-gear',
            'feedback_submitted': 'bi-chat-square-text',
        }
        return activity_icons.get(self.activity_type, 'bi-circle')


class VolunteerReport(models.Model):
    """
    Reports submitted by volunteers.
    """
    REPORT_TYPES = [
        ('daily', _('Daily Report')),
        ('weekly', _('Weekly Report')),
        ('monthly', _('Monthly Report')),
        ('project', _('Project Report')),
        ('incident', _('Incident Report')),
        ('feedback', _('Feedback Report')),
        ('hours', _('Hours Report')),
        ('expense', _('Expense Report')),
    ]

    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('revision_needed', _('Revision Needed')),
    ]

    volunteer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='volunteer_reports',
        limit_choices_to={'role': 'volunteer'}
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    task = models.ForeignKey(
        VolunteerTask, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reports'
    )
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    hours_worked = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    achievements = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)
    attachments = models.JSONField(blank=True, null=True)  # Store file paths/URLs
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_reports'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Volunteer Report')
        verbose_name_plural = _('Volunteer Reports')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.volunteer.get_full_name()}"

    def get_status_display_class(self):
        """Get CSS class for status display."""
        status_classes = {
            'draft': 'secondary',
            'submitted': 'warning',
            'under_review': 'info',
            'approved': 'success',
            'rejected': 'danger',
            'revision_needed': 'warning',
        }
        return status_classes.get(self.status, 'secondary')

    def can_edit(self):
        """Check if report can be edited."""
        return self.status in ['draft', 'revision_needed']

    def can_submit(self):
        """Check if report can be submitted."""
        return self.status == 'draft'


class VolunteerSkill(models.Model):
    """
    Skills and competencies of volunteers.
    """
    PROFICIENCY_LEVELS = [
        (1, _('Beginner')),
        (2, _('Novice')),
        (3, _('Intermediate')),
        (4, _('Advanced')),
        (5, _('Expert')),
    ]

    volunteer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='volunteer_skills',
        limit_choices_to={'role': 'volunteer'}
    )
    skill_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True)
    proficiency_level = models.IntegerField(
        choices=PROFICIENCY_LEVELS,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    years_experience = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    certification = models.CharField(max_length=200, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_skills'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Volunteer Skill')
        verbose_name_plural = _('Volunteer Skills')
        unique_together = ['volunteer', 'skill_name']
        ordering = ['category', 'skill_name']

    def __str__(self):
        return f"{self.volunteer.get_full_name()} - {self.skill_name} ({self.get_proficiency_level_display()})"


class VolunteerAvailability(models.Model):
    """
    Volunteer availability schedule.
    """
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]

    volunteer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='availability_schedule',
        limit_choices_to={'role': 'volunteer'}
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    max_hours_per_day = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.25)]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Volunteer Availability')
        verbose_name_plural = _('Volunteer Availability')
        unique_together = ['volunteer', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.volunteer.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class VolunteerEvent(models.Model):
    """
    Events that volunteers can participate in.
    """
    EVENT_TYPES = [
        ('health_camp', _('Health Camp')),
        ('food_drive', _('Food Drive')),
        ('education', _('Education Event')),
        ('renovation', _('Renovation Project')),
        ('training', _('Training Workshop')),
        ('fundraising', _('Fundraising Event')),
        ('awareness', _('Awareness Campaign')),
        ('community', _('Community Outreach')),
        ('environmental', _('Environmental Initiative')),
        ('other', _('Other')),
    ]

    STATUS_CHOICES = [
        ('upcoming', _('Upcoming')),
        ('ongoing', _('Ongoing')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('postponed', _('Postponed')),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='other')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='upcoming')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=300)
    location_details = models.TextField(blank=True)
    volunteers_needed = models.PositiveIntegerField(default=0)
    volunteers_registered = models.ManyToManyField(
        User,
        through='VolunteerEventRegistration',
        related_name='registered_events'
    )
    organizer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events'
    )
    requirements = models.TextField(blank=True, help_text="Special requirements or skills needed")
    equipment_provided = models.TextField(blank=True, help_text="Equipment or materials provided")
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    is_featured = models.BooleanField(default=False)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    max_volunteers = models.PositiveIntegerField(null=True, blank=True)
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.25)]
    )
    image = models.URLField(blank=True, help_text="Event image URL")
    attachments = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Volunteer Event')
        verbose_name_plural = _('Volunteer Events')
        ordering = ['start_date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%d %b %Y')}"

    @property
    def registration_count(self):
        """Get current registration count."""
        return self.volunteers_registered.count()

    @property
    def can_register(self):
        """Check if event is open for registration."""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'upcoming' and
            (not self.registration_deadline or now <= self.registration_deadline) and
            (not self.max_volunteers or self.registration_count < self.max_volunteers)
        )

    @property
    def is_full(self):
        """Check if event has reached maximum volunteers."""
        return self.max_volunteers and self.registration_count >= self.max_volunteers

    def get_status_display_class(self):
        """Get CSS class for status display."""
        status_classes = {
            'upcoming': 'primary',
            'ongoing': 'success',
            'completed': 'secondary',
            'cancelled': 'danger',
            'postponed': 'warning',
        }
        return status_classes.get(self.status, 'secondary')


class VolunteerEventRegistration(models.Model):
    """
    Registration of volunteers for events.
    """
    ATTENDANCE_CHOICES = [
        ('registered', _('Registered')),
        ('confirmed', _('Confirmed')),
        ('attended', _('Attended')),
        ('no_show', _('No Show')),
        ('cancelled', _('Cancelled')),
    ]

    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_registrations'
    )
    event = models.ForeignKey(
        VolunteerEvent,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    attendance_status = models.CharField(
        max_length=15,
        choices=ATTENDANCE_CHOICES,
        default='registered'
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    hours_contributed = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    feedback = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    dietary_restrictions = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Event Registration')
        verbose_name_plural = _('Event Registrations')
        unique_together = ['volunteer', 'event']
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.volunteer.get_full_name()} - {self.event.title}"


class VolunteerResource(models.Model):
    """
    Resources available to volunteers.
    """
    RESOURCE_TYPES = [
        ('handbook', _('Handbook')),
        ('guide', _('Guide')),
        ('training', _('Training Material')),
        ('policy', _('Policy Document')),
        ('form', _('Form Template')),
        ('toolkit', _('Toolkit')),
        ('manual', _('Manual')),
        ('video', _('Video Resource')),
        ('presentation', _('Presentation')),
        ('other', _('Other')),
    ]

    ACCESS_LEVELS = [
        ('public', _('Public')),
        ('volunteer', _('Volunteers Only')),
        ('coordinator', _('Coordinators Only')),
        ('admin', _('Admin Only')),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='other')
    access_level = models.CharField(max_length=15, choices=ACCESS_LEVELS, default='volunteer')
    file_url = models.URLField(blank=True, help_text="Direct link to the resource file")
    file_size = models.CharField(max_length=20, blank=True, help_text="File size (e.g., 2.4 MB)")
    download_count = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    version = models.CharField(max_length=20, blank=True)
    author = models.CharField(max_length=100, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_resources'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Volunteer Resource')
        verbose_name_plural = _('Volunteer Resources')
        ordering = ['-is_featured', '-last_updated', 'title']

    def __str__(self):
        return self.title

    def increment_download_count(self):
        """Increment download counter."""
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def get_file_extension(self):
        """Get file extension from URL."""
        if self.file_url:
            import os
            return os.path.splitext(self.file_url)[1].lower()
        return ''

    def get_file_icon(self):
        """Get appropriate icon for file type."""
        extension = self.get_file_extension()
        icon_map = {
            '.pdf': 'fas fa-file-pdf',
            '.doc': 'fas fa-file-word',
            '.docx': 'fas fa-file-word',
            '.xls': 'fas fa-file-excel',
            '.xlsx': 'fas fa-file-excel',
            '.ppt': 'fas fa-file-powerpoint',
            '.pptx': 'fas fa-file-powerpoint',
            '.mp4': 'fas fa-file-video',
            '.avi': 'fas fa-file-video',
            '.mov': 'fas fa-file-video',
            '.jpg': 'fas fa-file-image',
            '.jpeg': 'fas fa-file-image',
            '.png': 'fas fa-file-image',
            '.gif': 'fas fa-file-image',
            '.zip': 'fas fa-file-archive',
            '.rar': 'fas fa-file-archive',
        }
        return icon_map.get(extension, 'fas fa-file')


class VolunteerResourceAccess(models.Model):
    """
    Track resource access and downloads by volunteers.
    """
    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resource_accesses'
    )
    resource = models.ForeignKey(
        VolunteerResource,
        on_delete=models.CASCADE,
        related_name='accesses'
    )
    access_type = models.CharField(
        max_length=10,
        choices=[
            ('view', _('Viewed')),
            ('download', _('Downloaded')),
        ],
        default='view'
    )
    access_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Resource Access')
        verbose_name_plural = _('Resource Accesses')
        ordering = ['-access_date']

    def __str__(self):
        return f"{self.volunteer.get_full_name()} - {self.resource.title} ({self.access_type})"
