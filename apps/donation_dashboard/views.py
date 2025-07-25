"""
Views for donation dashboard.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta, date
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from decimal import Decimal
import uuid

from apps.accounts.permissions import (
    require_role,
    MultiRoleRequiredMixin
)
from .models import (
    Donation, Donor, DonationCampaign, 
    RecurringDonation, DonationReceipt
)

User = get_user_model()


class DonationManagerRequiredMixin(MultiRoleRequiredMixin):
    """Mixin to require donation manager or admin role."""
    allowed_roles = ['admin', 'donation']


@require_role(['admin', 'donation'])
def donation_dashboard(request):
    """
    Main donation dashboard view.
    """
    # Dashboard statistics
    total_donations = Donation.objects.filter(status='completed').count()
    total_amount = Donation.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_donors = Donor.objects.filter(status='active').count()
    total_campaigns = DonationCampaign.objects.filter(status='active').count()
    
    # Monthly statistics
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_donations = Donation.objects.filter(
        status='completed',
        donation_date__gte=current_month
    ).count()
    
    monthly_amount = Donation.objects.filter(
        status='completed',
        donation_date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Recent donations
    recent_donations = Donation.objects.filter(
        status='completed'
    ).select_related('donor', 'campaign').order_by('-donation_date')[:10]
    
    # Top donors
    top_donors = Donor.objects.filter(
        status='active'
    ).order_by('-total_donated')[:5]
    
    # Campaign performance
    campaign_performance = DonationCampaign.objects.filter(
        status='active'
    ).annotate(
        progress=Sum('donations__amount') * 100 / Sum('target_amount')
    ).order_by('-total_raised')[:5]
    
    # Donation trends (last 12 months)
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_trends = []
    for i in range(12):
        month_start = twelve_months_ago.replace(day=1) + timedelta(days=32*i)
        month_start = month_start.replace(day=1)
        next_month = month_start.replace(day=28) + timedelta(days=4)
        next_month = next_month.replace(day=1)
        
        month_total = Donation.objects.filter(
            status='completed',
            donation_date__gte=month_start,
            donation_date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        monthly_trends.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(month_total)
        })
    
    # Payment method distribution
    payment_methods = Donation.objects.filter(
        status='completed',
        donation_date__gte=current_month
    ).values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    # Recurring donations
    active_recurring = RecurringDonation.objects.filter(status='active').count()
    recurring_monthly_value = RecurringDonation.objects.filter(
        status='active'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Average donation amount
    avg_donation = Donation.objects.filter(
        status='completed'
    ).aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
    
    context = {
        'total_donations': total_donations,
        'total_amount': total_amount,
        'total_donors': total_donors,
        'total_campaigns': total_campaigns,
        'monthly_donations': monthly_donations,
        'monthly_amount': monthly_amount,
        'recent_donations': recent_donations,
        'top_donors': top_donors,
        'campaign_performance': campaign_performance,
        'monthly_trends': monthly_trends,
        'payment_methods': payment_methods,
        'active_recurring': active_recurring,
        'recurring_monthly_value': recurring_monthly_value,
        'avg_donation': avg_donation,
    }
    
    return render(request, 'donation_dashboard/dashboard.html', context)


class DonationListView(DonationManagerRequiredMixin, ListView):
    """
    List of donations with filtering and search.
    """
    model = Donation
    template_name = 'donation_dashboard/donation_list.html'
    context_object_name = 'donations'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Donation.objects.select_related(
            'donor', 'campaign'
        ).order_by('-donation_date')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by payment method
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by campaign
        campaign_id = self.request.GET.get('campaign')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(donation_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(donation_date__lte=date_to)
        
        # Filter by amount range
        amount_min = self.request.GET.get('amount_min')
        amount_max = self.request.GET.get('amount_max')
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(donor__first_name__icontains=search) |
                Q(donor__last_name__icontains=search) |
                Q(donor__email__icontains=search) |
                Q(donor__organization_name__icontains=search) |
                Q(transaction_id__icontains=search) |
                Q(donation_id__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['campaigns'] = DonationCampaign.objects.all()
        context['status_choices'] = Donation.STATUS_CHOICES
        context['payment_method_choices'] = Donation.PAYMENT_METHOD_CHOICES
        
        # Summary statistics for current filter
        filtered_donations = self.get_queryset()
        context['total_filtered'] = filtered_donations.count()
        context['total_amount_filtered'] = filtered_donations.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return context


@require_role(['admin', 'donation'])
def donor_management(request):
    """
    Manage donors with search and filtering.
    """
    # Get all donors with search and filtering
    donors = Donor.objects.all()
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        donors = donors.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(organization_name__icontains=search)
        )
    
    # Filter by donor type
    donor_type = request.GET.get('donor_type')
    if donor_type:
        donors = donors.filter(donor_type=donor_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        donors = donors.filter(status=status)
    
    # Sort options
    sort_by = request.GET.get('sort', '-total_donated')
    donors = donors.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(donors, 25)
    page_number = request.GET.get('page')
    donors_page = paginator.get_page(page_number)
    
    # Statistics
    total_donors = Donor.objects.count()
    active_donors = Donor.objects.filter(status='active').count()
    major_donors = Donor.objects.filter(total_donated__gte=1000).count()
    
    context = {
        'donors': donors_page,
        'total_donors': total_donors,
        'active_donors': active_donors,
        'major_donors': major_donors,
        'donor_type_choices': Donor.DONOR_TYPE_CHOICES,
        'status_choices': Donor.STATUS_CHOICES,
    }
    
    return render(request, 'donation_dashboard/donor_management.html', context)


@require_role(['admin', 'donation'])
def donation_reports(request):
    """
    Generate and view donation reports.
    """
    # Date range for reports
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from:
        date_from = timezone.now().replace(day=1).date()
    if not date_to:
        date_to = timezone.now().date()
    
    # Base queryset for reports
    donations = Donation.objects.filter(
        status='completed',
        donation_date__date__gte=date_from,
        donation_date__date__lte=date_to
    )
    
    # Summary statistics
    total_donations = donations.count()
    total_amount = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    avg_donation = donations.aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
    
    # Donor statistics
    unique_donors = donations.values('donor').distinct().count()
    new_donors = donations.filter(
        donor__first_donation_date__date__gte=date_from
    ).values('donor').distinct().count()
    
    # Campaign performance
    campaign_totals = donations.filter(
        campaign__isnull=False
    ).values('campaign__name').annotate(
        total_amount=Sum('amount'),
        donor_count=Count('donor', distinct=True),
        donation_count=Count('id')
    ).order_by('-total_amount')
    
    # Payment method breakdown
    payment_breakdown = donations.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    # Donation size analysis
    donation_ranges = [
        ('Under $25', donations.filter(amount__lt=25).count()),
        ('$25 - $99', donations.filter(amount__gte=25, amount__lt=100).count()),
        ('$100 - $499', donations.filter(amount__gte=100, amount__lt=500).count()),
        ('$500 - $999', donations.filter(amount__gte=500, amount__lt=1000).count()),
        ('$1,000+', donations.filter(amount__gte=1000).count()),
    ]
    
    # Monthly trends within date range
    monthly_data = donations.extra(
        select={'month': 'strftime("%%Y-%%m", donation_date)'}
    ).values('month').annotate(
        total_amount=Sum('amount'),
        donation_count=Count('id'),
        donor_count=Count('donor', distinct=True)
    ).order_by('month')
    
    # Top donors in period
    top_donors_period = donations.values(
        'donor__first_name', 'donor__last_name', 'donor__organization_name'
    ).annotate(
        total_donated=Sum('amount'),
        donation_count=Count('id')
    ).order_by('-total_donated')[:10]
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_donations': total_donations,
        'total_amount': total_amount,
        'avg_donation': avg_donation,
        'unique_donors': unique_donors,
        'new_donors': new_donors,
        'campaign_totals': campaign_totals,
        'payment_breakdown': payment_breakdown,
        'donation_ranges': donation_ranges,
        'monthly_data': monthly_data,
        'top_donors_period': top_donors_period,
    }
    
    return render(request, 'donation_dashboard/reports.html', context)


@require_role(['admin', 'donation'])
def receipt_generation(request):
    """
    Generate and manage donation receipts.
    """
    # Get receipts with filtering
    receipts = DonationReceipt.objects.select_related(
        'donation', 'donation__donor'
    ).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        receipts = receipts.filter(status=status)
    
    # Filter by tax year
    tax_year = request.GET.get('tax_year')
    if tax_year:
        receipts = receipts.filter(tax_year=tax_year)
    
    # Search by donor or receipt number
    search = request.GET.get('search')
    if search:
        receipts = receipts.filter(
            Q(receipt_number__icontains=search) |
            Q(donation__donor__first_name__icontains=search) |
            Q(donation__donor__last_name__icontains=search) |
            Q(donation__donor__email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(receipts, 25)
    page_number = request.GET.get('page')
    receipts_page = paginator.get_page(page_number)
    
    # Statistics
    total_receipts = DonationReceipt.objects.count()
    pending_receipts = DonationReceipt.objects.filter(status='pending').count()
    sent_receipts = DonationReceipt.objects.filter(status='sent').count()
    
    # Donations without receipts (completed donations without receipt)
    donations_without_receipts = Donation.objects.filter(
        status='completed',
        is_tax_deductible=True,
        receipt__isnull=True
    ).count()
    
    context = {
        'receipts': receipts_page,
        'total_receipts': total_receipts,
        'pending_receipts': pending_receipts,
        'sent_receipts': sent_receipts,
        'donations_without_receipts': donations_without_receipts,
        'status_choices': DonationReceipt.STATUS_CHOICES,
    }
    
    return render(request, 'donation_dashboard/receipt_generation.html', context)


@require_role(['admin', 'donation'])
def recurring_donations(request):
    """
    Manage recurring donations.
    """
    # Get recurring donations with filtering
    recurring = RecurringDonation.objects.select_related(
        'donor', 'campaign'
    ).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        recurring = recurring.filter(status=status)
    
    # Filter by frequency
    frequency = request.GET.get('frequency')
    if frequency:
        recurring = recurring.filter(frequency=frequency)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        recurring = recurring.filter(
            Q(donor__first_name__icontains=search) |
            Q(donor__last_name__icontains=search) |
            Q(donor__email__icontains=search) |
            Q(donor__organization_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(recurring, 25)
    page_number = request.GET.get('page')
    recurring_page = paginator.get_page(page_number)
    
    # Statistics
    total_recurring = RecurringDonation.objects.count()
    active_recurring = RecurringDonation.objects.filter(status='active').count()
    monthly_recurring_value = RecurringDonation.objects.filter(
        status='active'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Upcoming payments (next 30 days)
    upcoming_payments = RecurringDonation.objects.filter(
        status='active',
        next_payment_date__lte=timezone.now().date() + timedelta(days=30)
    ).order_by('next_payment_date')[:10]
    
    # Failed payments that need attention
    failed_payments = RecurringDonation.objects.filter(
        status='failed',
        failed_attempts__gte=1
    ).order_by('-failed_attempts')[:10]
    
    context = {
        'recurring_donations': recurring_page,
        'total_recurring': total_recurring,
        'active_recurring': active_recurring,
        'monthly_recurring_value': monthly_recurring_value,
        'upcoming_payments': upcoming_payments,
        'failed_payments': failed_payments,
        'status_choices': RecurringDonation.STATUS_CHOICES,
        'frequency_choices': RecurringDonation.FREQUENCY_CHOICES,
    }
    
    return render(request, 'donation_dashboard/recurring_donations.html', context)


@require_role(['admin', 'donation'])
def generate_receipt(request, donation_id):
    """
    Generate receipt for a specific donation.
    """
    donation = get_object_or_404(Donation, id=donation_id, status='completed')
    
    # Create or get receipt
    receipt, created = DonationReceipt.objects.get_or_create(
        donation=donation,
        defaults={
            'tax_deductible_amount': donation.amount,
            'tax_year': donation.donation_date.year,
        }
    )
    
    if created or receipt.status == 'pending':
        receipt.generate_receipt()
        messages.success(request, f'Receipt generated for donation {donation.donation_id}')
    
    return redirect('donation_dashboard:receipt_generation')


@require_role(['admin', 'donation'])
def send_receipt(request, receipt_id):
    """
    Send receipt via email.
    """
    receipt = get_object_or_404(DonationReceipt, id=receipt_id)
    
    if receipt.status == 'generated':
        receipt.send_receipt()
        messages.success(request, f'Receipt {receipt.receipt_number} sent successfully')
    else:
        messages.error(request, 'Receipt must be generated before sending')
    
    return redirect('donation_dashboard:receipt_generation')


@require_role(['admin', 'donation'])
def donation_detail(request, donation_id):
    """
    View detailed information about a specific donation.
    """
    donation = get_object_or_404(
        Donation.objects.select_related('donor', 'campaign'),
        donation_id=donation_id
    )
    
    # Get related information
    donor_donations = Donation.objects.filter(
        donor=donation.donor,
        status='completed'
    ).exclude(id=donation.id).order_by('-donation_date')[:5]
    
    context = {
        'donation': donation,
        'donor_donations': donor_donations,
    }
    
    return render(request, 'donation_dashboard/donation_detail.html', context)


@require_role(['admin', 'donation'])
def donor_detail(request, donor_id):
    """
    View detailed information about a specific donor.
    """
    donor = get_object_or_404(Donor, donor_id=donor_id)
    
    # Get donor's donations
    donations = donor.donations.filter(
        status='completed'
    ).order_by('-donation_date')
    
    # Get recurring donations
    recurring_donations = donor.recurring_donations.all()
    
    # Pagination for donations
    paginator = Paginator(donations, 10)
    page_number = request.GET.get('page')
    donations_page = paginator.get_page(page_number)
    
    context = {
        'donor': donor,
        'donations': donations_page,
        'recurring_donations': recurring_donations,
    }
    
    return render(request, 'donation_dashboard/donor_detail.html', context)


@require_role(['admin', 'donation'])
def export_donations(request):
    """
    Export donations data to CSV.
    """
    import csv
    from django.http import HttpResponse
    
    # Get filtered donations
    donations = Donation.objects.filter(status='completed').select_related('donor', 'campaign')
    
    # Apply filters from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        donations = donations.filter(donation_date__gte=date_from)
    if date_to:
        donations = donations.filter(donation_date__lte=date_to)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="donations_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Donation ID', 'Donor Name', 'Email', 'Amount', 'Currency',
        'Payment Method', 'Campaign', 'Date', 'Status', 'Anonymous'
    ])
    
    for donation in donations:
        writer.writerow([
            donation.donation_id,
            donation.donor.full_name,
            donation.donor.email,
            donation.amount,
            donation.currency,
            donation.get_payment_method_display(),
            donation.campaign.name if donation.campaign else 'General Fund',
            donation.donation_date.strftime('%Y-%m-%d %H:%M'),
            donation.get_status_display(),
            'Yes' if donation.is_anonymous else 'No'
        ])
    
    return response


# Donor-facing views
@login_required
def donor_dashboard(request):
    """
    New donor-facing dashboard with enhanced UI.
    """
    # Check if user has donation role
    if request.user.role != 'donation':
        messages.error(request, 'Access denied. This area is for donors only.')
        return redirect('login')
    
    # Get or create donor profile for the current user
    donor, created = Donor.objects.get_or_create(
        email=request.user.email,
        defaults={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'donor_type': 'individual',
        }
    )
    
    # Update donor stats if new
    if created or donor.donation_count == 0:
        donor.update_donation_stats()
    
    # Dashboard statistics
    total_donated = donor.total_donated or Decimal('0.00')
    donation_count = donor.donation_count or 0
    
    # Recent donations (last 4 for dashboard)
    recent_donations = donor.donations.filter(
        status='completed'
    ).select_related('campaign').order_by('-donation_date')[:4]
    
    # All donations for history
    all_donations = donor.donations.filter(
        status='completed'
    ).select_related('campaign').order_by('-donation_date')
    
    # Supported campaigns count
    supported_campaigns = donor.donations.filter(
        status='completed',
        campaign__isnull=False
    ).values('campaign').distinct().count()
    
    # Active campaigns for donation
    active_campaigns = DonationCampaign.objects.filter(
        status='active',
        is_public=True
    ).order_by('-is_featured', '-created_at')
    
    # Prepare stats for frontend
    stats = {
        'total_donated': float(total_donated),
        'donation_count': donation_count,
        'campaigns_supported': supported_campaigns,
    }
    
    context = {
        'donor': donor,
        'stats': stats,
        'recent_donations': recent_donations,
        'all_donations': all_donations,
        'active_campaigns': active_campaigns,
        'user': request.user,
    }
    
    return render(request, 'donation_dashboard/donor_dashboard_new.html', context)


@login_required
def donor_history(request):
    """
    Donor's donation history page.
    """
    # Get or create donor profile
    donor, created = Donor.objects.get_or_create(
        email=request.user.email,
        defaults={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'donor_type': 'individual',
        }
    )
    
    # Get all donations for this donor
    donations = donor.donations.select_related('campaign').order_by('-donation_date')
    
    # Filter by status if requested
    status_filter = request.GET.get('status', 'completed')
    if status_filter:
        donations = donations.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(donations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Donation statistics
    completed_donations = donor.donations.filter(status='completed')
    yearly_total = completed_donations.filter(
        donation_date__year=timezone.now().year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'donor': donor,
        'page_obj': page_obj,
        'yearly_total': yearly_total,
        'status_choices': Donation.STATUS_CHOICES,
        'current_status': status_filter,
    }
    
    return render(request, 'donation_dashboard/donor_history.html', context)


@login_required
def make_donation(request):
    """
    Process donation via AJAX for the new dashboard.
    """
    if request.method == 'POST':
        try:
            # Check if user has donation role
            if request.user.role != 'donation':
                return JsonResponse({'success': False, 'error': f'Access denied. Current role: {request.user.role}. Required: donation'})
            
            # Get or create donor
            donor, created = Donor.objects.get_or_create(
                email=request.user.email,
                defaults={
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'donor_type': 'individual',
                }
            )
            
            # Get form data
            amount = Decimal(request.POST.get('amount'))
            campaign_id = request.POST.get('campaign')
            
            # Validate amount
            if amount < 100:
                return JsonResponse({'success': False, 'error': 'Minimum donation amount is ₹100'})
            
            # Get campaign if specified
            campaign = None
            if campaign_id:
                try:
                    campaign = DonationCampaign.objects.get(id=campaign_id, status='active')
                except DonationCampaign.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Selected campaign is not available'})
            
            # Generate unique transaction ID
            transaction_id = f"TX-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
            
            # Create donation record
            donation = Donation.objects.create(
                donor=donor,
                campaign=campaign,
                amount=amount,
                currency='INR',  # Set currency to Indian Rupees
                payment_method='credit_card',  # Default for now
                is_anonymous=False,
                status='completed',  # In real app, this would be 'processing' until payment confirmation
                transaction_id=transaction_id,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                source='website'
            )
            
            # Create receipt
            receipt = DonationReceipt.objects.create(
                donation=donation,
                tax_deductible_amount=amount,
                tax_year=timezone.now().year,
                status='generated'
            )
            
            # Update donor and campaign statistics
            donor.update_donation_stats()
            if campaign:
                campaign.update_campaign_stats()
            
            return JsonResponse({
                'success': True, 
                'message': f'Thank you for your ₹{amount} donation!',
                'transaction_id': donation.transaction_id
            })
            
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Please enter a valid donation amount'})
        except Exception as e:
            # Log the actual error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Donation processing error: {str(e)}")
            return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required  
def download_receipt(request, donation_id):
    """
    Download tax receipt for a donation.
    """
    # Get donation belonging to current user
    try:
        donor = Donor.objects.get(email=request.user.email)
        donation = donor.donations.get(donation_id=donation_id, status='completed')
        receipt = donation.receipt
        
        # Increment download count
        receipt.download_count += 1
        receipt.save()
        
        # In a real implementation, this would serve the actual PDF file
        # For now, we'll redirect back with a success message
        messages.success(request, f'Receipt {receipt.receipt_number} downloaded successfully.')
        return redirect('donation_dashboard:donor_history')
        
    except (Donor.DoesNotExist, Donation.DoesNotExist, DonationReceipt.DoesNotExist):
        messages.error(request, 'Receipt not found or access denied.')
        return redirect('donation_dashboard:donor_history')


@login_required
def donation_impact(request):
    """
    Show donor their impact and how their donations are being used.
    """
    try:
        donor = Donor.objects.get(email=request.user.email)
    except Donor.DoesNotExist:
        messages.error(request, 'Donor profile not found.')
        return redirect('donation_dashboard:donor_dashboard')
    
    # Get donation statistics
    completed_donations = donor.donations.filter(status='completed')
    
    # Campaign contributions
    campaign_contributions = completed_donations.filter(
        campaign__isnull=False
    ).values('campaign__name').annotate(
        total_contributed=Sum('amount'),
        donation_count=Count('id')
    ).order_by('-total_contributed')
    
    # Monthly giving pattern
    monthly_giving = completed_donations.extra(
        select={'month': 'strftime("%%Y-%%m", donation_date)'}
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('month')
    
    # Yearly totals
    yearly_totals = completed_donations.extra(
        select={'year': 'strftime("%%Y", donation_date)'}
    ).values('year').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('year')
    
    context = {
        'donor': donor,
        'campaign_contributions': campaign_contributions,
        'monthly_giving': list(monthly_giving),
        'yearly_totals': yearly_totals,
    }
    
    return render(request, 'donation_dashboard/donor_impact.html', context)
