"""
Views for campaign manager dashboard.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, Max
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.accounts.permissions import require_role
User = get_user_model()
from apps.donation_dashboard.models import (
    DonationCampaign, Donation, Donor, CampaignActivity
)


@require_role(['admin', 'campaign'])
@login_required
def campaign_manager_dashboard(request):
    """
    Main campaign manager dashboard view.
    """
    # Check if user has campaign manager role
    if request.user.role not in ['admin', 'campaign']:
        messages.error(request, 'Access denied. This area is for campaign managers only.')
        return redirect('login')
    
    # Filter campaigns managed by current user (if not admin)
    if request.user.role == 'admin':
        campaigns_queryset = DonationCampaign.objects.all()
    else:
        campaigns_queryset = DonationCampaign.objects.filter(manager=request.user)
    
    # Active campaigns
    active_campaigns = campaigns_queryset.filter(status='active')
    
    # Calculate dashboard statistics
    total_campaigns = campaigns_queryset.count()
    active_campaigns_count = active_campaigns.count()
    
    # Total raised across all campaigns
    total_raised = campaigns_queryset.aggregate(
        total=Sum('total_raised')
    )['total'] or Decimal('0.00')
    
    # Average completion percentage
    campaigns_with_progress = [
        campaign for campaign in active_campaigns 
        if campaign.target_amount > 0
    ]
    if campaigns_with_progress:
        avg_completion = sum(
            campaign.progress_percentage for campaign in campaigns_with_progress
        ) / len(campaigns_with_progress)
    else:
        avg_completion = 0
    
    # Real volunteer count from user accounts
    volunteers_assigned = User.objects.filter(role='volunteer').count()
    
    # Recent activities
    recent_activities = CampaignActivity.objects.filter(
        campaign__in=campaigns_queryset
    ).select_related('campaign', 'user')[:10]
    
    # Recent donations for campaigns
    recent_donations = Donation.objects.filter(
        campaign__in=campaigns_queryset,
        status='completed'
    ).select_related('donor', 'campaign').order_by('-donation_date')[:10]
    
    # Fundraising statistics
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_donations = Donation.objects.filter(
        campaign__in=campaigns_queryset,
        status='completed',
        donation_date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # New donors this month
    new_donors = Donor.objects.filter(
        donations__campaign__in=campaigns_queryset,
        donations__status='completed',
        first_donation_date__gte=current_month
    ).distinct().count()
    
    # Mock conversion and growth rates
    conversion_rate = 18  # Mock data
    growth_rate = 32  # Mock data
    
    # Prepare context
    stats = {
        'active_campaigns': active_campaigns_count,
        'total_raised': float(total_raised),
        'volunteers_assigned': volunteers_assigned,
        'avg_completion': avg_completion,
    }
    
    fundraising_stats = {
        'monthly_donations': float(monthly_donations),
        'new_donors': new_donors,
        'conversion_rate': conversion_rate,
        'growth_rate': growth_rate,
    }
    
    # Add volunteer counts to active campaigns (mock data)
    for i, campaign in enumerate(active_campaigns):
        campaign.set_volunteer_count((i % 5) + 5)  # 5-9 volunteers per campaign
    
    # All campaigns for campaigns section
    all_campaigns = campaigns_queryset.order_by('-created_at')
    for i, campaign in enumerate(all_campaigns):
        campaign.set_volunteer_count((i % 5) + 5)
    
    context = {
        'stats': stats,
        'active_campaigns': active_campaigns[:5],  # Limit for dashboard table
        'all_campaigns': all_campaigns,
        'recent_activities': recent_activities,
        'recent_donations': recent_donations,
        'fundraising_stats': fundraising_stats,
        'user': request.user,
    }
    
    return render(request, 'campaign_dashboard/campaign_manager_dashboard.html', context)


@require_role(['admin', 'campaign'])
@login_required  
def create_campaign_activity(request, campaign_id, activity_type, description):
    """
    Helper function to create campaign activities.
    """
    try:
        campaign = DonationCampaign.objects.get(id=campaign_id)
        CampaignActivity.objects.create(
            campaign=campaign,
            activity_type=activity_type,
            description=description,
            user=request.user
        )
    except DonationCampaign.DoesNotExist:
        pass


@require_role(['admin', 'campaign'])
@require_POST
def create_campaign(request):
    """
    Create a new campaign via AJAX.
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        target_amount = request.POST.get('target_amount', '0')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        campaign_type = request.POST.get('campaign_type', 'general')
        
        # Validate required fields
        if not name:
            return JsonResponse({'success': False, 'error': 'Campaign name is required'})
        
        if not description:
            return JsonResponse({'success': False, 'error': 'Campaign description is required'})
        
        try:
            target_amount = Decimal(target_amount)
            if target_amount <= 0:
                return JsonResponse({'success': False, 'error': 'Target amount must be greater than 0'})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid target amount'})
        
        # Create campaign
        campaign = DonationCampaign.objects.create(
            name=name,
            description=description,
            target_amount=target_amount,
            start_date=start_date if start_date else timezone.now(),
            end_date=end_date if end_date else None,
            campaign_type=campaign_type,
            manager=request.user,
            status='active'
        )
        
        # Create activity log
        CampaignActivity.objects.create(
            campaign=campaign,
            activity_type='campaign_created',
            description=f"Campaign '{name}' created with target of ₹{target_amount:,.0f}",
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f"Campaign '{name}' created successfully!",
            'campaign_id': campaign.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error creating campaign: {str(e)}'})


@require_role(['admin', 'campaign'])
@login_required
def manage_campaign(request, campaign_id):
    """
    Campaign management page with editing capabilities.
    """
    # Get campaign (ensure user has permission)
    if request.user.role == 'admin':
        campaign = get_object_or_404(DonationCampaign, campaign_id=campaign_id)
    else:
        campaign = get_object_or_404(DonationCampaign, campaign_id=campaign_id, manager=request.user)
    
    # Get campaign statistics
    donations = campaign.donations.filter(status='completed')
    total_donated = donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    donor_count = donations.values('donor').distinct().count()
    recent_donations = donations.select_related('donor').order_by('-donation_date')[:10]
    
    # Monthly donation data for charts
    current_month = timezone.now().replace(day=1)
    monthly_data = []
    for i in range(6):  # Last 6 months
        month_start = current_month - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        month_total = donations.filter(
            donation_date__gte=month_start,
            donation_date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(month_total)
        })
    
    context = {
        'campaign': campaign,
        'total_donated': total_donated,
        'donor_count': donor_count,
        'recent_donations': recent_donations,
        'monthly_data': list(reversed(monthly_data)),
        'progress_percentage': campaign.progress_percentage,
    }
    
    return render(request, 'campaign_dashboard/manage_campaign.html', context)


@require_role(['admin', 'campaign'])
@login_required
def campaign_details(request, campaign_id):
    """
    Detailed view of campaign with analytics.
    """
    # Get campaign (ensure user has permission)
    if request.user.role == 'admin':
        campaign = get_object_or_404(DonationCampaign, campaign_id=campaign_id)
    else:
        campaign = get_object_or_404(DonationCampaign, campaign_id=campaign_id, manager=request.user)
    
    # Detailed analytics
    donations = campaign.donations.filter(status='completed')
    
    # Donation analytics
    avg_donation = donations.aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
    largest_donation = donations.aggregate(max=Max('amount'))['max'] or Decimal('0.00')
    
    # Top donors
    top_donors = donations.values(
        'donor__first_name', 'donor__last_name', 'donor__email'
    ).annotate(
        total_donated=Sum('amount'),
        donation_count=Count('id')
    ).order_by('-total_donated')[:5]
    
    # Recent activities
    recent_activities = CampaignActivity.objects.filter(
        campaign=campaign
    ).select_related('user').order_by('-created_at')[:10]
    
    context = {
        'campaign': campaign,
        'donations': donations.order_by('-donation_date')[:20],
        'avg_donation': avg_donation,
        'largest_donation': largest_donation,
        'top_donors': top_donors,
        'recent_activities': recent_activities,
        'progress_percentage': campaign.progress_percentage,
    }
    
    return render(request, 'campaign_dashboard/campaign_details.html', context)


def log_donation_activity(sender, instance, created, **kwargs):
    """
    Signal handler to log donation activities.
    """
    if instance.status == 'completed' and instance.campaign:
        description = f"Received ₹{instance.amount:,.0f} donation from {instance.display_donor_name}"
        CampaignActivity.objects.create(
            campaign=instance.campaign,
            activity_type='donation_received',
            description=description,
            metadata={'donation_id': str(instance.donation_id), 'amount': float(instance.amount)}
        )
