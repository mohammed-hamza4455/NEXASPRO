"""
URL configuration for nexas_project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='root'),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/admin/', include('apps.admin_dashboard.urls')),
    path('dashboard/volunteer/', include('apps.volunteer_dashboard.urls')),
    path('dashboard/campaign/', include('apps.campaign_dashboard.urls')),
    path('dashboard/donation/', include('apps.donation_dashboard.urls')),
    # path('api/v1/', include('apps.accounts.urls', namespace='api')),  # Disabled for now
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error pages
handler404 = 'apps.accounts.views.custom_404'
handler500 = 'apps.accounts.views.custom_500'
