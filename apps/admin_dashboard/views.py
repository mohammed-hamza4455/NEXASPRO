"""
Views for admin dashboard.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse

from apps.accounts.permissions import AdminRequiredMixin, admin_required
try:
    from .models import SystemSettings, AdminNotification, AuditLog
except ImportError:
    # Handle case where models don't exist yet
    SystemSettings = None
    AdminNotification = None
    AuditLog = None

User = get_user_model()


class AdminDashboardView(AdminRequiredMixin):
    """
    Main admin dashboard view.
    """
    
    def get(self, request):
        # Get dashboard statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_today = User.objects.filter(created_at__date=timezone.now().date()).count()
        
        # User role distribution
        role_distribution = User.objects.values('role').annotate(count=Count('role'))
        
        # Recent notifications
        recent_notifications = []
        if AdminNotification:
            recent_notifications = AdminNotification.objects.filter(
                recipient=request.user,
                is_read=False
            )[:5]
        
        # Recent audit logs
        recent_activities = []
        if AuditLog:
            recent_activities = AuditLog.objects.select_related('user')[:10]
        
        # Login statistics for the last 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        daily_logins = User.objects.filter(
            last_login__gte=seven_days_ago
        ).extra(
            select={'day': 'date(last_login)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        context = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'new_users_today': new_users_today,
            'role_distribution': role_distribution,
            'recent_notifications': recent_notifications,
            'recent_activities': recent_activities,
            'daily_logins': daily_logins,
        }
        
        return render(request, 'admin/dashboard.html', context)


@admin_required
def admin_dashboard(request):
    """
    Function-based admin dashboard view.
    """
    # Get dashboard statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_today = User.objects.filter(created_at__date=timezone.now().date()).count()
    
    # User role counts
    admin_count = User.objects.filter(role='admin').count()
    campaign_manager_count = User.objects.filter(role='campaign').count()
    donation_manager_count = User.objects.filter(role='donation').count()
    volunteer_count = User.objects.filter(role='volunteer').count()
    
    # Recent users
    recent_users = User.objects.order_by('-created_at')[:10]
    
    # User role distribution
    role_distribution = User.objects.values('role').annotate(count=Count('role'))
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'new_users_today': new_users_today,
        'admin_count': admin_count,
        'campaign_manager_count': campaign_manager_count,
        'donation_manager_count': donation_manager_count,
        'volunteer_count': volunteer_count,
        'recent_users': recent_users,
        'role_distribution': list(role_distribution),
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@admin_required
def system_settings(request):
    """
    Manage system settings.
    """
    settings = []
    if SystemSettings:
        settings = SystemSettings.objects.filter(is_active=True).order_by('key')
    
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        description = request.POST.get('description', '')
        
        if key and value:
            setting, created = SystemSettings.objects.get_or_create(
                key=key,
                defaults={
                    'value': value,
                    'description': description,
                    'updated_by': request.user
                }
            )
            
            if not created:
                setting.value = value
                setting.description = description
                setting.updated_by = request.user
                setting.save()
            
            return JsonResponse({'success': True, 'message': 'Setting saved successfully'})
    
    context = {
        'settings': settings
    }
    
    return render(request, 'admin/system_settings.html', context)


@admin_required
def user_analytics(request):
    """
    User analytics and reports.
    """
    # User registration trends
    thirty_days_ago = timezone.now() - timedelta(days=30)
    registration_trend = User.objects.filter(
        created_at__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Active users by role
    active_by_role = User.objects.filter(
        is_active=True
    ).values('role').annotate(count=Count('role'))
    
    # Users by department
    department_stats = User.objects.exclude(
        department__isnull=True
    ).exclude(
        department__exact=''
    ).values('department').annotate(count=Count('id')).order_by('-count')[:10]
    
    context = {
        'registration_trend': list(registration_trend),
        'active_by_role': list(active_by_role),
        'department_stats': list(department_stats),
    }
    
    return render(request, 'admin/user_analytics.html', context)


@admin_required
def notifications_list(request):
    """
    List and manage admin notifications.
    """
    notifications = AdminNotification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Mark as read if requested
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = AdminNotification.objects.get(
                    id=notification_id,
                    recipient=request.user
                )
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save()
                return JsonResponse({'success': True})
            except AdminNotification.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Notification not found'})
    
    context = {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count()
    }
    
    return render(request, 'admin/notifications.html', context)


@admin_required
def audit_logs(request):
    """
    View audit logs.
    """
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    
    # Filter by user if requested
    user_id = request.GET.get('user_id')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Filter by action if requested
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    # Filter by date range if requested
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_choices': AuditLog.ACTION_CHOICES,
        'users': User.objects.filter(is_staff=True),
    }
    
    return render(request, 'admin/audit_logs.html', context)


@admin_required
def dashboard_api_stats(request):
    """
    API endpoint for dashboard statistics (AJAX).
    """
    # Real-time statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    online_users = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(minutes=15)
    ).count()
    
    # Recent activity count
    recent_activities = AuditLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    data = {
        'total_users': total_users,
        'active_users': active_users,
        'online_users': online_users,
        'recent_activities': recent_activities,
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(data)
