"""
Models for campaign dashboard functionality.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class Campaign(models.Model):
    """
    Campaign model for tracking campaign information.
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('paused', _('Paused')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Campaign manager who owns this campaign
    manager = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='managed_campaigns',
        limit_choices_to={'role': 'campaign'}
    )
    
    # Dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Budget and targets
    budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Campaign budget in USD')
    )
    target_volunteers = models.PositiveIntegerField(
        default=0,
        help_text=_('Target number of volunteers needed')
    )
    target_donations = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Target donation amount in USD')
    )
    
    # Location and contact
    location = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=17, blank=True)
    
    # Social media
    website_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    # Images
    featured_image = models.ImageField(
        upload_to='campaigns/images/',
        blank=True,
        null=True,
        help_text=_('Featured image for the campaign')
    )
    
    # Status tracking
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        """Check if campaign is currently active."""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now <= self.end_date
        )

    @property
    def days_remaining(self):
        """Calculate days remaining in campaign."""
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0

    @property
    def progress_percentage(self):
        """Calculate campaign progress based on time elapsed."""
        if not self.start_date or not self.end_date:
            return 0
        
        now = timezone.now()
        if now < self.start_date:
            return 0
        elif now > self.end_date:
            return 100
        
        total_duration = (self.end_date - self.start_date).total_seconds()
        elapsed_duration = (now - self.start_date).total_seconds()
        return min(100, max(0, (elapsed_duration / total_duration) * 100))


class CampaignGoal(models.Model):
    """
    Specific goals for campaigns.
    """
    GOAL_TYPE_CHOICES = [
        ('volunteers', _('Volunteers')),
        ('donations', _('Donations')),
        ('events', _('Events')),
        ('outreach', _('Outreach')),
        ('custom', _('Custom')),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=50, default='count')
    
    # Tracking
    is_active = models.BooleanField(default=True)
    deadline = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Campaign Goal')
        verbose_name_plural = _('Campaign Goals')
        ordering = ['campaign', '-created_at']

    def __str__(self):
        return f"{self.campaign.name} - {self.title}"

    @property
    def completion_percentage(self):
        """Calculate goal completion percentage."""
        if self.target_value == 0:
            return 0
        return min(100, (float(self.current_value) / float(self.target_value)) * 100)

    @property
    def is_completed(self):
        """Check if goal is completed."""
        return self.current_value >= self.target_value


class CampaignMetrics(models.Model):
    """
    Tracking campaign performance metrics.
    """
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    
    # Volunteer metrics
    volunteers_registered = models.PositiveIntegerField(default=0)
    volunteers_active = models.PositiveIntegerField(default=0)
    volunteer_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Donation metrics
    donations_count = models.PositiveIntegerField(default=0)
    donations_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Outreach metrics
    events_held = models.PositiveIntegerField(default=0)
    people_reached = models.PositiveIntegerField(default=0)
    social_media_reach = models.PositiveIntegerField(default=0)
    website_visits = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    email_opens = models.PositiveIntegerField(default=0)
    email_clicks = models.PositiveIntegerField(default=0)
    social_shares = models.PositiveIntegerField(default=0)
    social_likes = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Campaign Metrics')
        verbose_name_plural = _('Campaign Metrics')
        unique_together = ['campaign', 'date']
        ordering = ['campaign', '-date']

    def __str__(self):
        return f"{self.campaign.name} - {self.date}"


class CampaignVolunteer(models.Model):
    """
    Volunteers assigned to campaigns.
    """
    STATUS_CHOICES = [
        ('invited', _('Invited')),
        ('accepted', _('Accepted')),
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('completed', _('Completed')),
        ('declined', _('Declined')),
    ]

    ROLE_CHOICES = [
        ('volunteer', _('Volunteer')),
        ('coordinator', _('Coordinator')),
        ('lead', _('Team Lead')),
        ('specialist', _('Specialist')),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_volunteers')
    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='volunteer_campaigns',
        limit_choices_to={'role': 'volunteer'}
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='invited')
    volunteer_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='volunteer')
    
    # Assignment details
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_volunteers'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    
    # Skills and notes
    skills_required = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Tracking
    hours_committed = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    hours_logged = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Campaign Volunteer')
        verbose_name_plural = _('Campaign Volunteers')
        unique_together = ['campaign', 'volunteer']
        ordering = ['campaign', 'volunteer_role', '-assigned_date']

    def __str__(self):
        return f"{self.volunteer.get_full_name()} - {self.campaign.name}"

    @property
    def is_active(self):
        """Check if volunteer assignment is active."""
        return self.status == 'active'


class CampaignUpdate(models.Model):
    """
    Progress updates and news for campaigns.
    """
    UPDATE_TYPE_CHOICES = [
        ('progress', _('Progress Update')),
        ('news', _('News')),
        ('milestone', _('Milestone')),
        ('announcement', _('Announcement')),
        ('alert', _('Alert')),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=200)
    content = models.TextField()
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPE_CHOICES, default='progress')
    
    # Author and publication
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='campaign_updates')
    is_published = models.BooleanField(default=False)
    publish_date = models.DateTimeField(blank=True, null=True)
    
    # Visibility
    is_public = models.BooleanField(default=True)
    notify_volunteers = models.BooleanField(default=False)
    send_email = models.BooleanField(default=False)
    
    # Media
    featured_image = models.ImageField(
        upload_to='campaigns/updates/',
        blank=True,
        null=True
    )
    
    # Engagement tracking
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Campaign Update')
        verbose_name_plural = _('Campaign Updates')
        ordering = ['campaign', '-created_at']

    def __str__(self):
        return f"{self.campaign.name} - {self.title}"

    def save(self, *args, **kwargs):
        if self.is_published and not self.publish_date:
            self.publish_date = timezone.now()
        super().save(*args, **kwargs)


class CampaignTask(models.Model):
    """
    Tasks associated with campaigns.
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

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_campaign_tasks'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    
    # Timing
    due_date = models.DateTimeField(blank=True, null=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Progress tracking
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Campaign Task')
        verbose_name_plural = _('Campaign Tasks')
        ordering = ['campaign', 'due_date', '-priority']

    def __str__(self):
        return f"{self.campaign.name} - {self.title}"

    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            self.progress_percentage = 100
        elif self.status != 'completed':
            self.completed_at = None
        
        # Auto-update status based on due date
        if self.is_overdue and self.status not in ['completed', 'cancelled']:
            self.status = 'overdue'
            
        super().save(*args, **kwargs)
