"""
Simple URL patterns for accounts app.
"""

from django.urls import path
from . import views_simple

app_name = 'accounts'

urlpatterns = [
    path('login/', views_simple.simple_login_view, name='login'),
    path('logout/', views_simple.simple_logout_view, name='logout'),
    path('dashboard/', views_simple.dashboard_redirect_simple, name='dashboard_redirect'),
]
