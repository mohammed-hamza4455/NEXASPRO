"""
URL patterns for accounts app.
"""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    
    # Password Reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Dashboard redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    
    # User Management URLs (Admin only)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('user/create/', views.UserCreateView.as_view(), name='user_create'),
    path('user/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('user/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('user/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('user/<int:user_id>/login-history/', views.user_login_history, name='user_login_history'),
    
    # Profile management
    path('profile/', views.profile_view, name='profile'),
    
    # AJAX endpoints
    path('ajax/user-search/', views.ajax_user_search, name='ajax_user_search'),
    
    # About page
    path('about/', views.about_view, name='about'),
]

# API URLs (if using DRF)
api_urlpatterns = [
    # Add API endpoints here if needed
    # path('auth/', include('rest_framework.urls')),
]
