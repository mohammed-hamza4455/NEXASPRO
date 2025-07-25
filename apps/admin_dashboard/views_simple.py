"""
Simple admin dashboard views.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def admin_dashboard_simple(request):
    """Simple admin dashboard view."""
    
    # Check if user is admin
    if not (hasattr(request.user, 'role') and request.user.role == 'admin'):
        return redirect('/accounts/login/')
    
    # Get basic statistics
    context = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'user': request.user,
    }
    
    return render(request, 'admin/dashboard_simple.html', context)
