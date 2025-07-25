"""
User models for NEXAS application with role-based access control.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Custom user manager for handling user creation with roles."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model with role-based access control for NEXAS platform.
    """
    
    class UserRole(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        VOLUNTEER = 'volunteer', _('Volunteer')
        CAMPAIGN = 'campaign', _('Campaign Manager')
        DONATION = 'donation', _('Donation Manager')

    # Remove username field and use email as the unique identifier
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # Additional user fields
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.VOLUNTEER,
        help_text=_('User role determines dashboard access and permissions.')
    )
    
    phone_number = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
            )
        ]
    )
    
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        help_text=_('Upload a profile picture (optional)')
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('User department or organization')
    )
    
    # Status fields
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active.')
    )
    
    email_verified = models.BooleanField(
        default=False,
        help_text=_('Designates whether the user has verified their email address.')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Security fields
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def get_dashboard_url(self):
        """Return the appropriate dashboard URL based on user role."""
        dashboard_urls = {
            self.UserRole.ADMIN: '/dashboard/admin/',
            self.UserRole.VOLUNTEER: '/dashboard/volunteer/',
            self.UserRole.CAMPAIGN: '/dashboard/campaign/',
            self.UserRole.DONATION: '/dashboard/donation/',
        }
        return dashboard_urls.get(self.role, '/dashboard/volunteer/')

    @property
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == self.UserRole.ADMIN

    @property
    def is_volunteer(self):
        """Check if user is a volunteer."""
        return self.role == self.UserRole.VOLUNTEER

    @property
    def is_campaign_manager(self):
        """Check if user is a campaign manager."""
        return self.role == self.UserRole.CAMPAIGN

    @property
    def is_donation_manager(self):
        """Check if user is a donation manager."""
        return self.role == self.UserRole.DONATION

    def has_permission(self, permission):
        """
        Check if user has specific permission based on role.
        This can be extended for more granular permissions.
        """
        role_permissions = {
            self.UserRole.ADMIN: [
                'can_create_users', 'can_delete_users', 'can_manage_all',
                'can_view_all_dashboards', 'can_manage_campaigns',
                'can_manage_donations', 'can_manage_volunteers'
            ],
            self.UserRole.CAMPAIGN: [
                'can_manage_campaigns', 'can_view_campaign_reports',
                'can_create_campaigns', 'can_edit_campaigns'
            ],
            self.UserRole.DONATION: [
                'can_manage_donations', 'can_view_donation_reports',
                'can_process_donations', 'can_generate_receipts'
            ],
            self.UserRole.VOLUNTEER: [
                'can_view_volunteer_dashboard', 'can_update_profile',
                'can_view_assigned_tasks'
            ]
        }
        
        return permission in role_permissions.get(self.role, [])


class UserProfile(models.Model):
    """
    Extended profile information for users.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text=_('Brief biography or description')
    )
    
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('City, State or Country')
    )
    
    website = models.URLField(
        blank=True,
        help_text=_('Personal or professional website')
    )
    
    linkedin_profile = models.URLField(
        blank=True,
        help_text=_('LinkedIn profile URL')
    )
    
    # Preferences
    email_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive email notifications')
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        help_text=_('Receive SMS notifications')
    )
    
    # Skills and interests (for volunteers)
    skills = models.TextField(
        blank=True,
        help_text=_('Comma-separated list of skills')
    )
    
    interests = models.TextField(
        blank=True,
        help_text=_('Areas of interest for volunteer work')
    )
    
    availability = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('When are you available for volunteer work?')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"{self.user.email} Profile"


class LoginHistory(models.Model):
    """
    Track user login history for security and analytics.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Geographic information (optional)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Success/failure tracking
    login_successful = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = _('Login History')
        verbose_name_plural = _('Login Histories')
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.email} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"
