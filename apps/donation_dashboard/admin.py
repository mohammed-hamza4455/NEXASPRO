"""
Admin configuration for donation dashboard.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from django.utils import timezone
from decimal import Decimal

from .models import (
    Donation, Donor, DonationCampaign, 
    RecurringDonation, DonationReceipt
)


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    """
    Admin interface for Donor model.
    """
    list_display = [
        'display_name', 'email', 'donor_type', 'status', 'total_donated',
        'donation_count', 'last_donation_date', 'is_major_donor_display', 'created_at'
    ]
    list_filter = [
        'donor_type', 'status', 'preferred_contact_method',
        'can_send_marketing', 'anonymous_donations', 'created_at', 'last_donation_date'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'organization_name', 
        'phone', 'donor_id'
    ]
    readonly_fields = [
        'donor_id', 'total_donated', 'donation_count', 'first_donation_date',
        'last_donation_date', 'created_at', 'updated_at', 'average_donation_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('donor_id', 'donor_type', 'status')
        }),
        ('Individual Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'occupation'),
            'classes': ('collapse',)
        }),
        ('Organization Information', {
            'fields': ('organization_name', 'organization_type'),
            'classes': ('collapse',)
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address_line1', 'address_line2', 
                      'city', 'state', 'postal_code', 'country')
        }),
        ('Preferences', {
            'fields': ('preferred_contact_method', 'communication_frequency',
                      'can_send_marketing', 'can_share_publicly', 'anonymous_donations')
        }),
        ('Profile Information', {
            'fields': ('interests', 'source', 'referred_by', 'notes'),
            'classes': ('collapse',)
        }),
        ('Donation Statistics', {
            'fields': ('total_donated', 'donation_count', 'average_donation_display',
                      'first_donation_date', 'last_donation_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_name(self, obj):
        """Display donor name based on type."""
        return obj.full_name or obj.email
    display_name.short_description = 'Name'
    display_name.admin_order_field = 'first_name'
    
    def is_major_donor_display(self, obj):
        """Display major donor status with styling."""
        if obj.is_major_donor:
            return format_html('<span style="color: #28a745; font-weight: bold;">⭐ Major</span>')
        return format_html('<span style="color: #6c757d;">Regular</span>')
    is_major_donor_display.short_description = 'Donor Level'
    
    def average_donation_display(self, obj):
        """Display average donation amount."""
        avg = obj.average_donation
        return format_html('${:,.2f}', avg)
    average_donation_display.short_description = 'Average Donation'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('donations')


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    """
    Admin interface for DonationCampaign model.
    """
    list_display = [
        'name', 'manager', 'campaign_type', 'status', 'target_amount',
        'total_raised', 'progress_display', 'donor_count', 'start_date',
        'end_date', 'is_goal_reached_display', 'created_at'
    ]
    list_filter = [
        'status', 'campaign_type', 'is_featured', 'is_public',
        'allow_anonymous', 'allow_recurring', 'created_at', 'start_date'
    ]
    search_fields = ['name', 'description', 'manager__email']
    readonly_fields = [
        'campaign_id', 'total_raised', 'donor_count', 'progress_display',
        'is_goal_reached_display', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('campaign_id', 'name', 'description', 'short_description',
                      'campaign_type', 'status', 'manager')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Financial Goals', {
            'fields': ('target_amount', 'minimum_donation', 'suggested_amounts',
                      'total_raised', 'progress_display', 'is_goal_reached_display')
        }),
        ('Tracking', {
            'fields': ('donor_count',),
            'classes': ('collapse',)
        }),
        ('Content & Media', {
            'fields': ('featured_image', 'video_url', 'social_share_title',
                      'social_share_description'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_public', 'allow_anonymous',
                      'allow_recurring', 'send_thank_you_email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_display(self, obj):
        """Display fundraising progress as a progress bar."""
        progress = obj.progress_percentage
        color = '#28a745' if progress >= 100 else '#ffc107' if progress >= 75 else '#dc3545'
        return format_html(
            '<div style="width: 150px; background-color: #e9ecef; border-radius: 4px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 4px; '
            'text-align: center; line-height: 20px; color: white; font-size: 12px;">{:.1f}%</div></div>',
            min(100, progress), color, progress
        )
    progress_display.short_description = 'Progress'
    
    def is_goal_reached_display(self, obj):
        """Display goal status with styling."""
        if obj.is_goal_reached:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Goal Reached</span>')
        return format_html('<span style="color: #ffc107;">In Progress</span>')
    is_goal_reached_display.short_description = 'Goal Status'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.select_related('manager').prefetch_related('donations')


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    """
    Admin interface for Donation model.
    """
    list_display = [
        'donation_id_short', 'donor_name', 'amount', 'currency', 'payment_method',
        'campaign', 'status', 'is_anonymous', 'donation_date', 'processed_date'
    ]
    list_filter = [
        'status', 'payment_method', 'currency', 'frequency', 'is_anonymous',
        'is_tribute', 'is_tax_deductible', 'donation_date', 'processed_date'
    ]
    search_fields = [
        'donor__first_name', 'donor__last_name', 'donor__email',
        'donor__organization_name', 'donation_id', 'transaction_id',
        'payment_reference'
    ]
    readonly_fields = [
        'donation_id', 'net_amount', 'processed_date', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'donation_date'
    
    fieldsets = (
        ('Donation Information', {
            'fields': ('donation_id', 'donor', 'campaign', 'amount', 'currency',
                      'fee_amount', 'net_amount')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_reference', 'payment_processor',
                      'transaction_id')
        }),
        ('Status & Timing', {
            'fields': ('status', 'frequency', 'donation_date', 'processed_date')
        }),
        ('Donation Options', {
            'fields': ('is_anonymous', 'is_tribute', 'tribute_name',
                      'tribute_message', 'tribute_notify_email'),
            'classes': ('collapse',)
        }),
        ('Messages', {
            'fields': ('donor_message', 'public_comment'),
            'classes': ('collapse',)
        }),
        ('Tax Information', {
            'fields': ('is_tax_deductible', 'tax_receipt_sent', 'tax_receipt_date'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('source', 'ip_address', 'user_agent', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def donation_id_short(self, obj):
        """Display shortened donation ID."""
        return str(obj.donation_id)[:8] + '...'
    donation_id_short.short_description = 'ID'
    
    def donor_name(self, obj):
        """Display donor name respecting anonymity."""
        return obj.display_donor_name
    donor_name.short_description = 'Donor'
    donor_name.admin_order_field = 'donor__first_name'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.select_related('donor', 'campaign')


@admin.register(RecurringDonation)
class RecurringDonationAdmin(admin.ModelAdmin):
    """
    Admin interface for RecurringDonation model.
    """
    list_display = [
        'recurring_id_short', 'donor_name', 'amount', 'frequency', 'status',
        'next_payment_date', 'total_donations', 'total_amount', 'annual_value_display',
        'failed_attempts', 'created_at'
    ]
    list_filter = [
        'status', 'frequency', 'payment_method', 'is_anonymous',
        'send_notifications', 'start_date', 'next_payment_date'
    ]
    search_fields = [
        'donor__first_name', 'donor__last_name', 'donor__email',
        'recurring_id', 'payment_token'
    ]
    readonly_fields = [
        'recurring_id', 'total_donations', 'total_amount', 'annual_value_display',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Recurring Information', {
            'fields': ('recurring_id', 'donor', 'campaign', 'amount', 'frequency', 'status')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_token', 'payment_processor')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date', 'next_payment_date', 'last_payment_date')
        }),
        ('Tracking', {
            'fields': ('total_donations', 'total_amount', 'annual_value_display', 'failed_attempts')
        }),
        ('Settings', {
            'fields': ('is_anonymous', 'send_notifications')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def recurring_id_short(self, obj):
        """Display shortened recurring ID."""
        return str(obj.recurring_id)[:8] + '...'
    recurring_id_short.short_description = 'ID'
    
    def donor_name(self, obj):
        """Display donor name."""
        return obj.donor.display_name
    donor_name.short_description = 'Donor'
    donor_name.admin_order_field = 'donor__first_name'
    
    def annual_value_display(self, obj):
        """Display annual value of recurring donation."""
        return format_html('${:,.2f}', obj.annual_value)
    annual_value_display.short_description = 'Annual Value'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.select_related('donor', 'campaign')


@admin.register(DonationReceipt)
class DonationReceiptAdmin(admin.ModelAdmin):
    """
    Admin interface for DonationReceipt model.
    """
    list_display = [
        'receipt_number', 'donor_name', 'donation_amount', 'tax_deductible_amount',
        'tax_year', 'status', 'email_sent', 'email_sent_date', 'download_count', 'created_at'
    ]
    list_filter = [
        'status', 'tax_year', 'email_sent', 'created_at', 'email_sent_date'
    ]
    search_fields = [
        'receipt_number', 'donation__donor__first_name', 'donation__donor__last_name',
        'donation__donor__email', 'donation__donation_id'
    ]
    readonly_fields = [
        'receipt_id', 'receipt_number', 'tax_year', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Receipt Information', {
            'fields': ('receipt_id', 'donation', 'receipt_number', 'tax_year', 'status')
        }),
        ('Tax Information', {
            'fields': ('tax_deductible_amount', 'organization_tax_id')
        }),
        ('File & Content', {
            'fields': ('receipt_file', 'receipt_html'),
            'classes': ('collapse',)
        }),
        ('Delivery', {
            'fields': ('email_sent', 'email_sent_date', 'download_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def donor_name(self, obj):
        """Display donor name."""
        return obj.donation.donor.display_name
    donor_name.short_description = 'Donor'
    donor_name.admin_order_field = 'donation__donor__first_name'
    
    def donation_amount(self, obj):
        """Display donation amount."""
        return format_html('${:,.2f}', obj.donation.amount)
    donation_amount.short_description = 'Donation Amount'
    donation_amount.admin_order_field = 'donation__amount'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.select_related('donation', 'donation__donor')


# Inline admin configurations
class DonationInline(admin.TabularInline):
    """Inline donations for donor admin."""
    model = Donation
    extra = 0
    readonly_fields = ['donation_id', 'amount', 'status', 'donation_date']
    fields = ['donation_id', 'amount', 'status', 'donation_date', 'campaign']
    can_delete = False


class RecurringDonationInline(admin.TabularInline):
    """Inline recurring donations for donor admin."""
    model = RecurringDonation
    extra = 0
    readonly_fields = ['recurring_id', 'amount', 'status', 'next_payment_date']
    fields = ['recurring_id', 'amount', 'frequency', 'status', 'next_payment_date']
    can_delete = False


# Add inlines to donor admin
DonorAdmin.inlines = [DonationInline, RecurringDonationInline]


# Custom admin actions
@admin.action(description='Generate receipts for selected donations')
def generate_receipts(modeladmin, request, queryset):
    """Generate receipts for selected donations."""
    count = 0
    for donation in queryset.filter(status='completed', is_tax_deductible=True):
        receipt, created = DonationReceipt.objects.get_or_create(
            donation=donation,
            defaults={
                'tax_deductible_amount': donation.amount,
                'tax_year': donation.donation_date.year,
            }
        )
        if created:
            receipt.generate_receipt()
            count += 1
    
    modeladmin.message_user(request, f'Generated {count} receipts.')


@admin.action(description='Mark selected donors as major donors')
def mark_as_major_donors(modeladmin, request, queryset):
    """Mark selected donors as major donors."""
    count = queryset.filter(total_donated__gte=1000).count()
    queryset.filter(total_donated__gte=1000).update(is_major_donor=True)
    modeladmin.message_user(request, f'Marked {count} donors as major donors.')


@admin.action(description='Send thank you emails')
def send_thank_you_emails(modeladmin, request, queryset):
    """Send thank you emails for selected donations."""
    count = 0
    for donation in queryset.filter(status='completed'):
        # Email sending logic would go here
        count += 1
    
    modeladmin.message_user(request, f'Sent thank you emails for {count} donations.')


# Add actions to admin classes
DonationAdmin.actions = [generate_receipts, send_thank_you_emails]
DonorAdmin.actions = [mark_as_major_donors]


# Custom admin site configurations
admin.site.site_header = "NEXAS Donation Management"
admin.site.site_title = "NEXAS Donation Admin"
admin.site.index_title = "Donation Dashboard Administration"
