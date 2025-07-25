"""
URL patterns for donation dashboard.
"""

from django.urls import path
from . import views

app_name = 'donation_dashboard'

urlpatterns = [
    # Main admin dashboard
    path('admin/', views.donation_dashboard, name='admin_dashboard'),
    
    # Donor-facing dashboard (public access)
    path('', views.donor_dashboard, name='donor_dashboard'),
    path('history/', views.donor_history, name='donor_history'),
    path('donate/', views.make_donation, name='make_donation'),
    path('impact/', views.donation_impact, name='donation_impact'),
    path('receipt/<uuid:donation_id>/', views.download_receipt, name='download_receipt'),
    
    # Admin donation management
    path('admin/donations/', views.DonationListView.as_view(), name='donation_list'),
    path('admin/donations/<uuid:donation_id>/', views.donation_detail, name='donation_detail'),
    path('admin/donations/export/', views.export_donations, name='export_donations'),
    
    # Admin donor management
    path('admin/donors/', views.donor_management, name='donor_management'),
    path('admin/donors/<uuid:donor_id>/', views.donor_detail, name='donor_detail'),
    
    # Admin reports
    path('admin/reports/', views.donation_reports, name='reports'),
    
    # Admin receipt management
    path('admin/receipts/', views.receipt_generation, name='receipt_generation'),
    path('admin/receipts/generate/<int:donation_id>/', views.generate_receipt, name='generate_receipt'),
    path('admin/receipts/send/<int:receipt_id>/', views.send_receipt, name='send_receipt'),
    
    # Admin recurring donations
    path('admin/recurring/', views.recurring_donations, name='recurring_donations'),
]
