"""
Custom middleware for NEXAS application.
"""

import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce role-based access control for dashboard URLs.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define role-based URL patterns
        self.role_urls = {
            'admin': ['/dashboard/admin/'],
            'volunteer': ['/dashboard/volunteer/'],
            'campaign': ['/dashboard/campaign/'],
            'donation': ['/dashboard/donation/']
        }
        
        # URLs that require admin access
        self.admin_only_urls = [
            '/accounts/users/',
            '/accounts/user/create/',
            '/accounts/user/update/',
            '/accounts/user/delete/',
        ]
        
        # Public URLs that don't require authentication
        self.public_urls = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password-reset/',
            '/accounts/password-reset-done/',
            '/admin/',
            '/static/',
            '/media/',
        ]

    def process_request(self, request):
        """Process incoming requests for role-based access control."""
        
        # Skip middleware for public URLs
        if any(request.path.startswith(url) for url in self.public_urls):
            return None
        
        # Skip middleware for non-authenticated users (let Django handle it)
        if not request.user.is_authenticated:
            return None
        
        user = request.user
        current_path = request.path
        
        # Check admin-only URLs
        if any(current_path.startswith(url) for url in self.admin_only_urls):
            if not user.is_admin:
                logger.warning(f"Unauthorized admin access attempt by {user.email} to {current_path}")
                messages.error(request, 'You do not have permission to access this page.')
                return redirect(user.get_dashboard_url())
        
        # Check role-based dashboard access
        for role, urls in self.role_urls.items():
            if any(current_path.startswith(url) for url in urls):
                if user.role != role:
                    logger.warning(f"Unauthorized dashboard access attempt by {user.email} ({user.role}) to {current_path}")
                    messages.error(request, f'You do not have access to the {role} dashboard.')
                    return redirect(user.get_dashboard_url())
                break
        
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    """
    
    def process_response(self, request, response):
        """Add security headers to response."""
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add Content Security Policy for enhanced security
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        return response


class LoginTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user activity and login sessions.
    """
    
    def process_request(self, request):
        """Track user activity for authenticated users."""
        
        if request.user.is_authenticated:
            # Update last activity timestamp
            from django.utils import timezone
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Check for session expiry based on inactivity
            if 'last_activity' in request.session:
                try:
                    last_activity = timezone.datetime.fromisoformat(request.session['last_activity'])
                    if timezone.now() - last_activity > timezone.timedelta(hours=2):
                        # Session expired due to inactivity
                        from django.contrib.auth import logout
                        logout(request)
                        messages.info(request, 'Your session has expired due to inactivity.')
                        return redirect('accounts:login')
                except (ValueError, TypeError):
                    # Invalid timestamp, clear it
                    del request.session['last_activity']
        
        return None
