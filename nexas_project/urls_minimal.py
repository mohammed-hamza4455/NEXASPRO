"""
Minimal URL configuration for nexas_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='root'),
    path('accounts/', include('apps.accounts.urls_simple')),
    path('dashboard/admin/', include('apps.admin_dashboard.urls_simple')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
