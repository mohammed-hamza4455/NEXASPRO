"""
Signals for accounts app.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.utils import timezone
import logging

from .models import User, UserProfile, LoginHistory

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)
        logger.info(f"UserProfile created for user: {instance.email}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login."""
    try:
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Create login history record
        LoginHistory.objects.create(
            user=user,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_key=request.session.session_key,
            login_successful=True
        )
        
        logger.info(f"User {user.email} logged in from IP: {ip}")
        
    except Exception as e:
        logger.error(f"Error logging user login: {e}")


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Log failed login attempt."""
    try:
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        username = credentials.get('username')
        
        # Try to find the user to log the failed attempt
        if username:
            try:
                user = User.objects.get(email=username)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    login_successful=False,
                    failure_reason='Invalid credentials'
                )
            except User.DoesNotExist:
                pass
        
        logger.warning(f"Failed login attempt for username: {username} from IP: {ip}")
        
    except Exception as e:
        logger.error(f"Error logging failed login: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout."""
    try:
        if user:
            # Update logout time in most recent login record
            login_record = LoginHistory.objects.filter(
                user=user,
                session_key=request.session.session_key,
                logout_time__isnull=True
            ).first()
            
            if login_record:
                login_record.logout_time = timezone.now()
                login_record.save()
            
            logger.info(f"User {user.email} logged out")
            
    except Exception as e:
        logger.error(f"Error logging user logout: {e}")


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up related data when a user is deleted."""
    try:
        # Delete profile picture if it exists
        if instance.profile_picture:
            instance.profile_picture.delete(save=False)
        
        logger.info(f"Cleaned up data for deleted user: {instance.email}")
        
    except Exception as e:
        logger.error(f"Error cleaning up user data: {e}")
