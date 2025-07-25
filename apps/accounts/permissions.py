"""
Role-based permissions and mixins for NEXAS application.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework import permissions


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires user to have specific role(s).
    """
    required_roles = []  # List of allowed roles
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.required_roles and request.user.role not in self.required_roles:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(request.user.get_dashboard_url())
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """
    Mixin that requires user to be an admin.
    """
    required_roles = ['admin']


class VolunteerRequiredMixin(RoleRequiredMixin):
    """
    Mixin that requires user to be a volunteer.
    """
    required_roles = ['volunteer']


class CampaignManagerRequiredMixin(RoleRequiredMixin):
    """
    Mixin that requires user to be a campaign manager.
    """
    required_roles = ['campaign']


class DonationManagerRequiredMixin(RoleRequiredMixin):
    """
    Mixin that requires user to be a donation manager.
    """
    required_roles = ['donation']


class MultiRoleRequiredMixin(RoleRequiredMixin):
    """
    Mixin that allows multiple roles access to a view.
    Usage: Set required_roles = ['admin', 'campaign'] in your view.
    """
    pass


class SameUserOrAdminMixin(LoginRequiredMixin):
    """
    Mixin that allows access to the user themselves or admin users.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Get the user object from URL parameter
        user_id = kwargs.get('pk') or kwargs.get('user_id')
        if user_id:
            if not (request.user.id == int(user_id) or request.user.is_admin):
                messages.error(request, 'You can only access your own information.')
                return redirect(request.user.get_dashboard_url())
        
        return super().dispatch(request, *args, **kwargs)


# DRF Permissions
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to owner or admin
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_admin
        
        # For user objects
        if hasattr(obj, 'email'):
            return obj == request.user or request.user.is_admin
        
        return False


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsVolunteerUser(permissions.BasePermission):
    """
    Allows access only to volunteer users.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_volunteer)


class IsCampaignManagerUser(permissions.BasePermission):
    """
    Allows access only to campaign manager users.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_campaign_manager)


class IsDonationManagerUser(permissions.BasePermission):
    """
    Allows access only to donation manager users.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_donation_manager)


class RoleBasedPermission(permissions.BasePermission):
    """
    Permission class that checks user roles dynamically.
    Usage: Add required_roles = ['admin', 'campaign'] to your view class.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        required_roles = getattr(view, 'required_roles', [])
        if not required_roles:
            return True  # No specific role required
        
        return request.user.role in required_roles


def require_role(allowed_roles):
    """
    Decorator to require specific role(s) for function-based views.
    
    Usage:
    @require_role(['admin'])
    def my_view(request):
        pass
    
    @require_role(['admin', 'campaign'])
    def my_view(request):
        pass
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect(request.user.get_dashboard_url())
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator to require admin role for function-based views.
    """
    return require_role(['admin'])(view_func)


def volunteer_required(view_func):
    """
    Decorator to require volunteer role for function-based views.
    """
    return require_role(['volunteer'])(view_func)


def campaign_manager_required(view_func):
    """
    Decorator to require campaign manager role for function-based views.
    """
    return require_role(['campaign'])(view_func)


def donation_manager_required(view_func):
    """
    Decorator to require donation manager role for function-based views.
    """
    return require_role(['donation'])(view_func)
