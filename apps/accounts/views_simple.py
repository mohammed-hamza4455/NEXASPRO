"""
Simple views for accounts app without DRF dependencies.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache


@csrf_protect
@never_cache
def simple_login_view(request):
    """Simple login view without class-based complexity."""
    
    if request.user.is_authenticated:
        # Redirect to appropriate dashboard based on user role
        if hasattr(request.user, 'role'):
            if request.user.role == 'admin':
                return redirect('/dashboard/admin/')
            elif request.user.role == 'volunteer':
                return redirect('/dashboard/volunteer/')
            elif request.user.role == 'campaign':
                return redirect('/dashboard/campaign/')
            elif request.user.role == 'donation':
                return redirect('/dashboard/donation/')
        return redirect('/dashboard/admin/')
    
    if request.method == 'POST':
        email = request.POST.get('username', '').strip()  # Using 'username' for email
        password = request.POST.get('password', '').strip()
        
        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')
                    
                    # Redirect based on role
                    if hasattr(user, 'role'):
                        if user.role == 'admin':
                            return redirect('/dashboard/admin/')
                        elif user.role == 'volunteer':
                            return redirect('/dashboard/volunteer/')
                        elif user.role == 'campaign':
                            return redirect('/dashboard/campaign/')
                        elif user.role == 'donation':
                            return redirect('/dashboard/donation/')
                    return redirect('/dashboard/admin/')
                else:
                    messages.error(request, 'This account has been deactivated.')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please enter both email and password.')
    
    return render(request, 'accounts/login_simple.html')


def simple_logout_view(request):
    """Simple logout view."""
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('/accounts/login/')


def dashboard_redirect_simple(request):
    """Redirect users to their appropriate dashboard."""
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    
    if hasattr(request.user, 'role'):
        if request.user.role == 'admin':
            return redirect('/dashboard/admin/')
        elif request.user.role == 'volunteer':
            return redirect('/dashboard/volunteer/')
        elif request.user.role == 'campaign':
            return redirect('/dashboard/campaign/')
        elif request.user.role == 'donation':
            return redirect('/dashboard/donation/')
    
    return redirect('/dashboard/admin/')
