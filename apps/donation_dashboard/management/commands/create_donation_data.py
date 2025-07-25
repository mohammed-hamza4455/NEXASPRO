"""
Management command to create sample donation data.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from apps.donation_dashboard.models import (
    Donor, DonationCampaign, Donation, DonationReceipt
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample donation data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing donation data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing donation data...')
            Donation.objects.all().delete()
            DonationReceipt.objects.all().delete()
            DonationCampaign.objects.all().delete()
            Donor.objects.all().delete()

        self.stdout.write('Creating sample donation data...')

        # Create or get admin user for managing campaigns
        admin_user, created = User.objects.get_or_create(
            email='admin@nexas.org',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'Created admin user: {admin_user.email}')

        # Create donor user
        donor_user, created = User.objects.get_or_create(
            email='donor@nexas.org',
            defaults={
                'first_name': 'John',
                'last_name': 'Donor',
                'role': 'donation',  # Donation dashboard access
            }
        )
        
        # If user exists but has wrong role, update it
        if not created and donor_user.role != 'donation':
            donor_user.role = 'donation'
            donor_user.save()
        if created:
            donor_user.set_password('donor123')
            donor_user.save()
            self.stdout.write(f'Created donor user: {donor_user.email}')

        # Create donor profile
        donor, created = Donor.objects.get_or_create(
            email=donor_user.email,
            defaults={
                'first_name': donor_user.first_name,
                'last_name': donor_user.last_name,
                'donor_type': 'individual',
                'phone': '+1234567890',
                'address_line1': '123 Donor Street',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'United States',
            }
        )
        if created:
            self.stdout.write(f'Created donor profile: {donor.full_name}')

        # Create sample campaigns
        campaigns_data = [
            {
                'name': 'Education Fund',
                'description': 'Supporting education for underprivileged children',
                'short_description': 'Providing educational resources and opportunities',
                'campaign_type': 'project',
                'target_amount': Decimal('50000.00'),
                'minimum_donation': Decimal('100.00'),
                'suggested_amounts': [100, 250, 500, 1000, 2500],
            },
            {
                'name': 'Health & Wellness',
                'description': 'Healthcare initiatives for communities in need',
                'short_description': 'Supporting health programs and medical care',
                'campaign_type': 'project',
                'target_amount': Decimal('75000.00'),
                'minimum_donation': Decimal('50.00'),
                'suggested_amounts': [50, 150, 300, 750, 1500],
            },
            {
                'name': 'Food for All',
                'description': 'Fighting hunger and providing nutritious meals',
                'short_description': 'Eliminating hunger in our communities',
                'campaign_type': 'emergency',
                'target_amount': Decimal('30000.00'),
                'minimum_donation': Decimal('25.00'),
                'suggested_amounts': [25, 75, 150, 500, 1000],
            },
            {
                'name': 'Environment Conservation',
                'description': 'Protecting our planet for future generations',
                'short_description': 'Environmental protection and sustainability',
                'campaign_type': 'project',
                'target_amount': Decimal('40000.00'),
                'minimum_donation': Decimal('50.00'),
                'suggested_amounts': [50, 125, 250, 600, 1200],
            },
            {
                'name': 'Disaster Relief',
                'description': 'Emergency response and disaster recovery support',
                'short_description': 'Helping communities recover from disasters',
                'campaign_type': 'emergency',
                'target_amount': Decimal('100000.00'),
                'minimum_donation': Decimal('25.00'),
                'suggested_amounts': [25, 100, 250, 1000, 2500],
            },
        ]

        campaigns = []
        for campaign_data in campaigns_data:
            campaign, created = DonationCampaign.objects.get_or_create(
                name=campaign_data['name'],
                defaults={
                    **campaign_data,
                    'manager': admin_user,
                    'status': 'active',
                    'start_date': timezone.now() - timedelta(days=30),
                    'end_date': timezone.now() + timedelta(days=90),
                    'is_featured': random.choice([True, False]),
                    'is_public': True,
                }
            )
            if created:
                campaigns.append(campaign)
                self.stdout.write(f'Created campaign: {campaign.name}')

        # Create sample donations
        donations_data = [
            {
                'amount': Decimal('5000.00'),
                'payment_method': 'credit_card',
                'campaign_name': 'Education Fund',
                'days_ago': 25,
            },
            {
                'amount': Decimal('2500.00'),
                'payment_method': 'paypal',
                'campaign_name': 'Health & Wellness',
                'days_ago': 45,
            },
            {
                'amount': Decimal('3000.00'),
                'payment_method': 'credit_card',
                'campaign_name': 'Food for All',
                'days_ago': 65,
            },
            {
                'amount': Decimal('2000.00'),
                'payment_method': 'bank_transfer',
                'campaign_name': 'Environment Conservation',
                'days_ago': 85,
            },
            {
                'amount': Decimal('1500.00'),
                'payment_method': 'paypal',
                'campaign_name': 'Disaster Relief',
                'days_ago': 105,
            },
            {
                'amount': Decimal('3500.00'),
                'payment_method': 'credit_card',
                'campaign_name': 'Education Fund',
                'days_ago': 125,
            },
        ]

        for i, donation_data in enumerate(donations_data):
            # Find campaign
            try:
                campaign = DonationCampaign.objects.get(name=donation_data['campaign_name'])
            except DonationCampaign.DoesNotExist:
                campaign = None

            # Create donation
            donation_date = timezone.now() - timedelta(days=donation_data['days_ago'])
            donation = Donation.objects.create(
                donor=donor,
                campaign=campaign,
                amount=donation_data['amount'],
                payment_method=donation_data['payment_method'],
                status='completed',
                transaction_id=f"TX-{donation_date.strftime('%Y%m%d')}-{i+1:04d}",
                donation_date=donation_date,
                processed_date=donation_date,
                is_tax_deductible=True,
                source='website',
            )

            # Create receipt
            receipt = DonationReceipt.objects.create(
                donation=donation,
                tax_deductible_amount=donation.amount,
                tax_year=donation_date.year,
                status='generated',
            )

            self.stdout.write(f'Created donation: ${donation.amount} to {campaign.name if campaign else "General Fund"}')

        # Update statistics for all donors and campaigns
        for donor in Donor.objects.all():
            donor.update_donation_stats()

        for campaign in DonationCampaign.objects.all():
            campaign.update_campaign_stats()

        # Create additional random donors and donations for more realistic data
        additional_donors_data = [
            {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@example.com'},
            {'first_name': 'Mike', 'last_name': 'Johnson', 'email': 'mike.johnson@example.com'},
            {'first_name': 'Sarah', 'last_name': 'Williams', 'email': 'sarah.williams@example.com'},
            {'first_name': 'David', 'last_name': 'Brown', 'email': 'david.brown@example.com'},
            {'first_name': 'Lisa', 'last_name': 'Davis', 'email': 'lisa.davis@example.com'},
        ]

        for donor_data in additional_donors_data:
            additional_donor, created = Donor.objects.get_or_create(
                email=donor_data['email'],
                defaults={
                    'first_name': donor_data['first_name'],
                    'last_name': donor_data['last_name'],
                    'donor_type': 'individual',
                    'status': 'active',
                }
            )
            
            if created:
                # Create 1-3 random donations for each donor
                num_donations = random.randint(1, 3)
                for _ in range(num_donations):
                    donation_amount = Decimal(random.choice([100, 250, 500, 750, 1000, 1500]))
                    campaign = random.choice(campaigns) if campaigns else None
                    payment_method = random.choice(['credit_card', 'paypal', 'bank_transfer'])
                    days_ago = random.randint(1, 180)
                    
                    donation_date = timezone.now() - timedelta(days=days_ago)
                    donation = Donation.objects.create(
                        donor=additional_donor,
                        campaign=campaign,
                        amount=donation_amount,
                        payment_method=payment_method,
                        status='completed',
                        transaction_id=f"TX-{donation_date.strftime('%Y%m%d%H%M%S')}-{additional_donor.id}",
                        donation_date=donation_date,
                        processed_date=donation_date,
                        is_tax_deductible=True,
                        source='website',
                    )
                    
                    # Create receipt
                    DonationReceipt.objects.create(
                        donation=donation,
                        tax_deductible_amount=donation.amount,
                        tax_year=donation_date.year,
                        status='generated',
                    )

                additional_donor.update_donation_stats()
                self.stdout.write(f'Created additional donor: {additional_donor.full_name}')

        # Final update of all statistics
        for campaign in DonationCampaign.objects.all():
            campaign.update_campaign_stats()

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample donation data!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Donor login: {donor_user.email} / donor123')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Admin login: {admin_user.email} / admin123')
        )
        self.stdout.write(
            self.style.SUCCESS('Visit /dashboard/donation/ to see the donor dashboard')
        )
