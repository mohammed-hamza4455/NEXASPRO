"""
Authentication and user management views for NEXAS application.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q

from .forms import CustomLoginForm, CustomUserCreationForm, CustomPasswordResetForm, UserProfileForm, UserUpdateForm
from .models import User, UserProfile, LoginHistory
from .permissions import RoleRequiredMixin

logger = logging.getLogger(__name__)


def about_view(request):
    """About page view."""
    return render(request, 'about.html')


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class CustomLoginView(LoginView):
    """
    Custom login view with role-based redirection and security logging.
    """
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Handle successful login."""
        user = form.get_user()
        login(self.request, user)
        
        # Update last login IP
        user.last_login_ip = get_client_ip(self.request)
        user.save(update_fields=['last_login_ip'])
        
        # Log successful login
        LoginHistory.objects.create(
            user=user,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            session_key=self.request.session.session_key,
            login_successful=True
        )
        
        logger.info(f"Successful login for user: {user.email} from IP: {get_client_ip(self.request)}")
        
        # Set remember me
        if form.cleaned_data.get('remember_me'):
            self.request.session.set_expiry(1209600)  # 2 weeks
        
        messages.success(self.request, f'Welcome back, {user.get_full_name()}!')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        """Handle failed login."""
        # Log failed login attempt
        username = form.cleaned_data.get('username')
        if username:
            try:
                user = User.objects.get(email=username)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=get_client_ip(self.request),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    login_successful=False,
                    failure_reason='Invalid credentials'
                )
            except User.DoesNotExist:
                pass
        
        logger.warning(f"Failed login attempt for email: {username} from IP: {get_client_ip(self.request)}")
        return super().form_invalid(form)

    def get_success_url(self):
        """Redirect user to appropriate dashboard based on role."""
        user = self.request.user
        return user.get_dashboard_url()


@login_required
def custom_logout_view(request):
    """Custom logout view with session cleanup."""
    user = request.user
    
    # Update logout time in login history
    try:
        login_record = LoginHistory.objects.filter(
            user=user,
            session_key=request.session.session_key,
            logout_time__isnull=True
        ).first()
        
        if login_record:
            login_record.logout_time = timezone.now()
            login_record.save()
    except Exception as e:
        logger.error(f"Error updating logout time: {e}")
    
    logger.info(f"User {user.email} logged out from IP: {get_client_ip(request)}")
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('accounts:login')


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view."""
    form_class = CustomPasswordResetForm
    template_name = 'accounts/forgot_password.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        """Log password reset request."""
        email = form.cleaned_data['email']
        logger.info(f"Password reset requested for email: {email} from IP: {get_client_ip(self.request)}")
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view."""
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view (Set Password)."""
    template_name = 'accounts/set_password.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        """Handle successful password reset."""
        response = super().form_valid(form)
        user = form.user
        logger.info(f"Password reset completed for user: {user.email} from IP: {get_client_ip(self.request)}")
        messages.success(self.request, 'Your password has been successfully updated!')
        return response


def is_admin(user):
    """Check if user is admin."""
    return user.is_authenticated and user.is_admin


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class UserCreateView(CreateView):
    """Admin view to create new users."""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_create.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        """Handle successful user creation."""
        try:
            response = super().form_valid(form)
            user = self.object
            logger.info(f"User {user.email} created by admin: {self.request.user.email}")
            messages.success(self.request, f'User {user.get_full_name()} created successfully!')
            
            # Handle AJAX requests
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'User {user.get_full_name()} created successfully!',
                    'user_id': user.id
                })
            return response
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            messages.error(self.request, 'An error occurred while creating the user.')
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred while creating the user.'
                }, status=400)
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission."""
        logger.warning(f"Invalid user creation form submitted by admin: {self.request.user.email}")
        
        # Handle AJAX requests
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(error) for error in field_errors]
            
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': errors
            }, status=400)
        
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class UserListView(ListView):
    """Admin view to list all users."""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter users based on search query."""
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(department__icontains=search_query)
            )
        
        role_filter = self.request.GET.get('role')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = User.UserRole.choices
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_role'] = self.request.GET.get('role', '')
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class UserUpdateView(UpdateView):
    """Admin view to update user information."""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_update.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Remove password fields for update
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        logger.info(f"User {user.email} updated by admin: {self.request.user.email}")
        messages.success(self.request, f'User {user.get_full_name()} updated successfully!')
        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class UserDeleteView(DeleteView):
    """Admin view to delete users."""
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            messages.error(request, "You cannot delete your own account!")
            return redirect('accounts:user_list')
        
        logger.info(f"User {user.email} deleted by admin: {request.user.email}")
        messages.success(request, f'User {user.get_full_name()} deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def profile_view(request):
    """User profile view and update."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard."""
    return redirect(request.user.get_dashboard_url())


@login_required
def ajax_user_search(request):
    """AJAX endpoint for user search."""
    if not request.user.is_admin:
        raise PermissionDenied
    
    query = request.GET.get('q', '')
    users = User.objects.filter(
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:10]
    
    results = [{
        'id': user.id,
        'email': user.email,
        'name': user.get_full_name(),
        'role': user.get_role_display()
    } for user in users]
    
    return JsonResponse({'results': results})


def custom_404(request, exception=None):
    """Custom 404 error page."""
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """Custom 500 error page."""
    return render(request, 'errors/500.html', status=500)


@login_required
def toggle_user_status(request, user_id):
    """AJAX endpoint to toggle user active status."""
    if not request.user.is_admin:
        raise PermissionDenied
    
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        return JsonResponse({'error': 'Cannot deactivate your own account'}, status=400)
    
    user.is_active = not user.is_active
    user.save()
    
    action = 'activated' if user.is_active else 'deactivated'
    logger.info(f"User {user.email} {action} by admin: {request.user.email}")
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'User {action} successfully'
    })


@login_required
def user_login_history(request, user_id):
    """View user login history (admin only)."""
    if not request.user.is_admin:
        raise PermissionDenied
    
    user = get_object_or_404(User, id=user_id)
    login_history = LoginHistory.objects.filter(user=user).order_by('-login_time')[:50]
    
    context = {
        'target_user': user,
        'login_history': login_history
    }
    return render(request, 'accounts/user_login_history.html', context)
