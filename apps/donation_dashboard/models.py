"""
Models for donation dashboard functionality.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Donor(models.Model):
    """
    Donor information and profiles.
    """
    DONOR_TYPE_CHOICES = [
        ('individual', _('Individual')),
        ('organization', _('Organization')),
        ('foundation', _('Foundation')),
        ('corporate', _('Corporate')),
        ('government', _('Government')),
    ]

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('blacklisted', _('Blacklisted')),
        ('prospect', _('Prospect')),
    ]

    # Basic Information
    donor_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    donor_type = models.CharField(max_length=20, choices=DONOR_TYPE_CHOICES, default='individual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Individual fields
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # Organization fields
    organization_name = models.CharField(max_length=200, blank=True)
    organization_type = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=17,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
        )]
    )
    
    # Address
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='United States')
    
    # Donor Preferences
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ('email', _('Email')),
            ('phone', _('Phone')),
            ('mail', _('Mail')),
            ('no_contact', _('No Contact')),
        ],
        default='email'
    )
    communication_frequency = models.CharField(
        max_length=20,
        choices=[
            ('weekly', _('Weekly')),
            ('monthly', _('Monthly')),
            ('quarterly', _('Quarterly')),
            ('annually', _('Annually')),
            ('never', _('Never')),
        ],
        default='monthly'
    )
    
    # Privacy and Marketing
    can_send_marketing = models.BooleanField(default=True)
    can_share_publicly = models.BooleanField(default=False)
    anonymous_donations = models.BooleanField(default=False)
    
    # Profile Information
    date_of_birth = models.DateField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True)
    interests = models.TextField(blank=True, help_text=_('Comma-separated interests'))
    notes = models.TextField(blank=True)
    
    # Tracking
    total_donated = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    donation_count = models.PositiveIntegerField(default=0)
    first_donation_date = models.DateTimeField(blank=True, null=True)
    last_donation_date = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    source = models.CharField(max_length=100, blank=True, help_text=_('How they found us'))
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Donor')
        verbose_name_plural = _('Donors')
        ordering = ['-total_donated', '-last_donation_date']

    def __str__(self):
        if self.donor_type == 'individual':
            return f"{self.first_name} {self.last_name}".strip() or self.email
        return self.organization_name or self.email

    @property
    def full_name(self):
        """Get full name for individual donors."""
        if self.donor_type == 'individual':
            return f"{self.first_name} {self.last_name}".strip()
        return self.organization_name

    @property
    def display_name(self):
        """Get display name based on privacy settings."""
        if self.anonymous_donations:
            return "Anonymous"
        return self.full_name or self.email

    @property
    def average_donation(self):
        """Calculate average donation amount."""
        if self.donation_count > 0:
            return self.total_donated / self.donation_count
        return Decimal('0.00')

    @property
    def is_major_donor(self):
        """Check if donor qualifies as major donor (>$1000 total)."""
        return self.total_donated >= Decimal('1000.00')

    def update_donation_stats(self):
        """Update donation statistics."""
        donations = self.donations.filter(status='completed')
        self.donation_count = donations.count()
        self.total_donated = donations.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        if donations.exists():
            self.first_donation_date = donations.earliest('created_at').created_at
            self.last_donation_date = donations.latest('created_at').created_at
        
        self.save(update_fields=['donation_count', 'total_donated', 'first_donation_date', 'last_donation_date'])


class DonationCampaign(models.Model):
    """
    Campaigns specifically for donations.
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('paused', _('Paused')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]

    CAMPAIGN_TYPE_CHOICES = [
        ('general', _('General Fund')),
        ('emergency', _('Emergency Response')),
        ('project', _('Specific Project')),
        ('memorial', _('Memorial Fund')),
        ('matching', _('Matching Gift')),
        ('peer_to_peer', _('Peer-to-Peer')),
    ]

    # Basic Information
    campaign_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Campaign Manager
    manager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='managed_donation_campaigns',
        limit_choices_to={'role__in': ['admin', 'donation']}
    )
    
    # Dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Financial Goals
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Target donation amount in USD')
    )
    minimum_donation = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    suggested_amounts = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of suggested donation amounts')
    )
    
    # Tracking
    total_raised = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    donor_count = models.PositiveIntegerField(default=0)
    
    # Content
    featured_image = models.ImageField(
        upload_to='campaigns/donations/',
        blank=True,
        null=True
    )
    video_url = models.URLField(blank=True)
    
    # Settings
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    allow_anonymous = models.BooleanField(default=True)
    allow_recurring = models.BooleanField(default=True)
    send_thank_you_email = models.BooleanField(default=True)
    
    # Social Media
    social_share_title = models.CharField(max_length=200, blank=True)
    social_share_description = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = _('Donation Campaign')
        verbose_name_plural = _('Donation Campaigns')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        """Check if campaign is currently active."""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now and
            (not self.end_date or now <= self.end_date)
        )

    @property
    def days_remaining(self):
        """Calculate days remaining in campaign."""
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return None

    @property
    def progress_percentage(self):
        """Calculate fundraising progress percentage."""
        if self.target_amount == 0:
            return 0
        return min(100, (float(self.total_raised) / float(self.target_amount)) * 100)

    @property
    def is_goal_reached(self):
        """Check if fundraising goal has been reached."""
        return self.total_raised >= self.target_amount

    def update_campaign_stats(self):
        """Update campaign statistics."""
        donations = self.donations.filter(status='completed')
        self.total_raised = donations.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        self.donor_count = donations.values('donor').distinct().count()
        self.save(update_fields=['total_raised', 'donor_count'])
    
    @property
    def progress_percentage(self):
        """Calculate campaign progress as percentage."""
        if self.target_amount <= 0:
            return 0
        return min(100, (float(self.total_raised) / float(self.target_amount)) * 100)
    
    @property
    def volunteer_count(self):
        """Get number of volunteers assigned to this campaign."""
        # This would require integration with volunteer dashboard
        # For now, return a default value
        return getattr(self, '_volunteer_count', 0)
    
    def set_volunteer_count(self, count):
        """Set volunteer count (helper for dashboard)."""
        self._volunteer_count = count


class Donation(models.Model):
    """
    Donation records with amounts, payment methods, status.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', _('Credit Card')),
        ('debit_card', _('Debit Card')),
        ('bank_transfer', _('Bank Transfer')),
        ('paypal', _('PayPal')),
        ('check', _('Check')),
        ('cash', _('Cash')),
        ('crypto', _('Cryptocurrency')),
        ('stock', _('Stock')),
        ('other', _('Other')),
    ]

    FREQUENCY_CHOICES = [
        ('one_time', _('One Time')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('annually', _('Annually')),
    ]

    # Basic Information
    donation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations')
    campaign = models.ForeignKey(
        DonationCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations'
    )
    
    # Financial Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='USD')
    fee_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Processing fees deducted')
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Amount after fees')
    )
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_reference = models.CharField(max_length=200, blank=True)
    payment_processor = models.CharField(max_length=100, blank=True)
    transaction_id = models.CharField(max_length=200, blank=True, unique=True)
    
    # Status and Timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='one_time')
    
    # Dates
    donation_date = models.DateTimeField(default=timezone.now)
    processed_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Donation Details
    is_anonymous = models.BooleanField(default=False)
    is_tribute = models.BooleanField(default=False)
    tribute_name = models.CharField(max_length=200, blank=True)
    tribute_message = models.TextField(blank=True)
    tribute_notify_email = models.EmailField(blank=True)
    
    # Donor Message
    donor_message = models.TextField(blank=True)
    public_comment = models.TextField(blank=True)
    
    # Tax Information
    is_tax_deductible = models.BooleanField(default=True)
    tax_receipt_sent = models.BooleanField(default=False)
    tax_receipt_date = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    source = models.CharField(max_length=100, blank=True, help_text=_('Donation source/channel'))
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Internal Notes
    internal_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Donation')
        verbose_name_plural = _('Donations')
        ordering = ['-donation_date']

    def __str__(self):
        return f"{self.donor} - ${self.amount} ({self.donation_date.strftime('%Y-%m-%d')})"

    def save(self, *args, **kwargs):
        # Calculate net amount
        self.net_amount = self.amount - self.fee_amount
        
        # Set processed date when status changes to completed
        if self.status == 'completed' and not self.processed_date:
            self.processed_date = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update donor and campaign statistics
        if self.status == 'completed':
            self.donor.update_donation_stats()
            if self.campaign:
                self.campaign.update_campaign_stats()

    @property
    def display_donor_name(self):
        """Get donor name for display, respecting anonymity."""
        if self.is_anonymous:
            return "Anonymous"
        return self.donor.display_name

    @property
    def is_recurring(self):
        """Check if this is a recurring donation."""
        return self.frequency != 'one_time'


class RecurringDonation(models.Model):
    """
    Monthly/yearly recurring donations.
    """
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('paused', _('Paused')),
        ('cancelled', _('Cancelled')),
        ('expired', _('Expired')),
        ('failed', _('Failed')),
    ]

    FREQUENCY_CHOICES = [
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('annually', _('Annually')),
    ]

    # Basic Information
    recurring_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='recurring_donations')
    campaign = models.ForeignKey(
        DonationCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_donations'
    )
    
    # Recurring Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=Donation.PAYMENT_METHOD_CHOICES)
    payment_token = models.CharField(max_length=200, blank=True)
    payment_processor = models.CharField(max_length=100, blank=True)
    
    # Scheduling
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    next_payment_date = models.DateField()
    last_payment_date = models.DateField(blank=True, null=True)
    
    # Tracking
    total_donations = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    failed_attempts = models.PositiveIntegerField(default=0)
    
    # Settings
    is_anonymous = models.BooleanField(default=False)
    send_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Recurring Donation')
        verbose_name_plural = _('Recurring Donations')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.donor} - ${self.amount} {self.frequency}"

    @property
    def is_active(self):
        """Check if recurring donation is active."""
        if self.status != 'active':
            return False
        if self.end_date and timezone.now().date() > self.end_date:
            return False
        return True

    @property
    def annual_value(self):
        """Calculate annual value of recurring donation."""
        frequency_multipliers = {
            'weekly': 52,
            'monthly': 12,
            'quarterly': 4,
            'annually': 1,
        }
        return self.amount * frequency_multipliers.get(self.frequency, 0)

    def calculate_next_payment_date(self):
        """Calculate the next payment date based on frequency."""
        from dateutil.relativedelta import relativedelta
        
        frequency_deltas = {
            'weekly': relativedelta(weeks=1),
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'annually': relativedelta(years=1),
        }
        
        if self.last_payment_date:
            base_date = self.last_payment_date
        else:
            base_date = self.start_date
            
        delta = frequency_deltas.get(self.frequency)
        if delta:
            return base_date + delta
        return base_date

    def process_payment(self):
        """Create a donation record for this recurring payment."""
        donation = Donation.objects.create(
            donor=self.donor,
            campaign=self.campaign,
            amount=self.amount,
            payment_method=self.payment_method,
            frequency=self.frequency,
            is_anonymous=self.is_anonymous,
            source='recurring',
            status='processing'
        )
        
        # Update recurring donation stats
        self.total_donations += 1
        self.total_amount += self.amount
        self.last_payment_date = timezone.now().date()
        self.next_payment_date = self.calculate_next_payment_date()
        self.save()
        
        return donation


class DonationReceipt(models.Model):
    """
    Receipt generation and tracking.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('generated', _('Generated')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
    ]

    # Basic Information
    receipt_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name='receipt')
    
    # Receipt Details
    receipt_number = models.CharField(max_length=50, unique=True)
    tax_year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tax Information
    tax_deductible_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_('Amount eligible for tax deduction')
    )
    organization_tax_id = models.CharField(max_length=50, blank=True)
    
    # File and Content
    receipt_file = models.FileField(
        upload_to='receipts/',
        blank=True,
        null=True
    )
    receipt_html = models.TextField(blank=True)
    
    # Delivery
    email_sent = models.BooleanField(default=False)
    email_sent_date = models.DateTimeField(blank=True, null=True)
    download_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Donation Receipt')
        verbose_name_plural = _('Donation Receipts')
        ordering = ['-created_at']

    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.donation.donor}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate receipt number: YYYY-XXXXXX
            year = self.donation.donation_date.year
            last_receipt = DonationReceipt.objects.filter(
                tax_year=year
            ).order_by('-receipt_number').first()
            
            if last_receipt and last_receipt.receipt_number:
                last_number = int(last_receipt.receipt_number.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.receipt_number = f"{year}-{new_number:06d}"
        
        if not self.tax_year:
            self.tax_year = self.donation.donation_date.year
            
        if not self.tax_deductible_amount:
            self.tax_deductible_amount = self.donation.amount
            
        super().save(*args, **kwargs)

    def generate_receipt(self):
        """Generate the receipt file."""
        # This would contain logic to generate PDF receipt
        # For now, just update status
        self.status = 'generated'
        self.save()

    def send_receipt(self):
        """Send receipt via email."""
        if self.status == 'generated' and not self.email_sent:
            # Email sending logic would go here
            self.email_sent = True
            self.email_sent_date = timezone.now()
            self.status = 'sent'
            self.save()


class CampaignActivity(models.Model):
    """
    Track activities related to campaigns for activity feed.
    """
    ACTIVITY_TYPE_CHOICES = [
        ('campaign_created', _('Campaign Created')),
        ('campaign_updated', _('Campaign Updated')),
        ('donation_received', _('Donation Received')),
        ('volunteer_joined', _('Volunteer Joined')),
        ('milestone_reached', _('Milestone Reached')),
        ('campaign_shared', _('Campaign Shared')),
        ('report_generated', _('Report Generated')),
        ('campaign_completed', _('Campaign Completed')),
    ]

    campaign = models.ForeignKey(
        DonationCampaign,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='campaign_activities',
        blank=True,
        null=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Campaign Activity')
        verbose_name_plural = _('Campaign Activities')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign.name} - {self.get_activity_type_display()}"

    @property
    def icon(self):
        """Get appropriate FontAwesome icon for activity type."""
        icon_map = {
            'campaign_created': 'fas fa-plus-circle',
            'campaign_updated': 'fas fa-edit',
            'donation_received': 'fas fa-rupee-sign',
            'volunteer_joined': 'fas fa-user-plus',
            'milestone_reached': 'fas fa-trophy',
            'campaign_shared': 'fas fa-share-alt',
            'report_generated': 'fas fa-file-alt',
            'campaign_completed': 'fas fa-check-circle',
        }
        return icon_map.get(self.activity_type, 'fas fa-info-circle')
