"""
Management command to create sample data for volunteer dashboard.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.volunteer_dashboard.models import (
    VolunteerTask, VolunteerActivity, VolunteerEvent, 
    VolunteerResource, VolunteerEventRegistration
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for volunteer dashboard testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            VolunteerTask.objects.all().delete()
            VolunteerActivity.objects.all().delete()
            VolunteerEvent.objects.all().delete()
            VolunteerResource.objects.all().delete()
            VolunteerEventRegistration.objects.all().delete()

        self.stdout.write('Creating sample data...')

        # Create or get admin user
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

        # Create or get volunteer user
        volunteer_user, created = User.objects.get_or_create(
            email='volunteer@nexas.org',
            defaults={
                'first_name': 'John',
                'last_name': 'Volunteer',
                'role': 'volunteer',
                'phone_number': '+1234567890',
            }
        )
        if created:
            volunteer_user.set_password('volunteer123')
            volunteer_user.save()
            self.stdout.write(f'Created volunteer user: {volunteer_user.email}')

        # Create sample tasks
        tasks_data = [
            {
                'title': 'Pack Relief Kits',
                'description': 'Prepare 200 relief kits for distribution in flood-affected areas. Each kit should contain essential items like rice, lentils, oil, and hygiene products.',
                'priority': 'high',
                'status': 'in_progress',
                'due_date': timezone.now() + timedelta(days=3),
                'estimated_hours': 4.0,
            },
            {
                'title': 'Event Setup',
                'description': 'Prepare venue for the upcoming health camp. Arrange chairs, tables, and medical equipment. Coordinate with medical team for their requirements.',
                'priority': 'high',
                'status': 'in_progress',
                'due_date': timezone.now() + timedelta(days=1),
                'estimated_hours': 3.0,
            },
            {
                'title': 'Donation Collection',
                'description': 'Collect donations from local businesses for the school renovation project. Document all contributions and issue receipts.',
                'priority': 'medium',
                'status': 'pending',
                'due_date': timezone.now() + timedelta(days=6),
                'estimated_hours': 6.0,
            },
            {
                'title': 'Volunteer Training',
                'description': 'Conduct training session for new volunteers on community outreach protocols and safety measures. Prepare training materials.',
                'priority': 'medium',
                'status': 'in_progress',
                'due_date': timezone.now() + timedelta(days=8),
                'estimated_hours': 5.0,
            },
            {
                'title': 'Social Media Campaign',
                'description': 'Create content and manage social media posts for the upcoming food drive event. Promote volunteer opportunities.',
                'priority': 'low',
                'status': 'in_progress',
                'due_date': timezone.now() + timedelta(days=2),
                'estimated_hours': 3.0,
            },
        ]

        for task_data in tasks_data:
            task, created = VolunteerTask.objects.get_or_create(
                title=task_data['title'],
                defaults={
                    **task_data,
                    'assigned_to': volunteer_user,
                    'assigned_by': admin_user,
                }
            )
            if created:
                self.stdout.write(f'Created task: {task.title}')

        # Create sample events
        events_data = [
            {
                'title': 'Community Food Drive',
                'description': 'NEXAS NGO is organizing a large-scale food collection and distribution event to support underprivileged families in our community. This event aims to provide essential food supplies to over 500 families affected by recent economic challenges.',
                'event_type': 'food_drive',
                'start_date': timezone.now() + timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=1, hours=7),
                'location': 'Community Center, Downtown',
                'volunteers_needed': 45,
                'max_volunteers': 50,
            },
            {
                'title': "Children's Health Camp",
                'description': 'Join NEXAS in providing free health checkups for children in low-income neighborhoods. This comprehensive health camp will include general checkups, vaccinations, dental examinations, and nutritional counseling.',
                'event_type': 'health_camp',
                'start_date': timezone.now() + timedelta(days=9),
                'end_date': timezone.now() + timedelta(days=9, hours=10),
                'location': 'City Park, West District',
                'volunteers_needed': 30,
                'max_volunteers': 35,
            },
            {
                'title': 'School Renovation Project',
                'description': 'NEXAS is leading a renovation project at Riverside Public School to improve learning conditions for over 300 students. Volunteers will participate in painting classrooms, repairing furniture, creating a reading corner, and improving playground facilities.',
                'event_type': 'renovation',
                'start_date': timezone.now() + timedelta(days=14),
                'end_date': timezone.now() + timedelta(days=14, hours=5),
                'location': 'Riverside Public School',
                'volunteers_needed': 25,
                'max_volunteers': 30,
            },
            {
                'title': 'Digital Literacy Workshop',
                'description': 'This NEXAS initiative focuses on bridging the digital divide by teaching basic computer skills to senior citizens and underprivileged youth. Volunteers will work one-on-one with participants to cover essential computer operations, internet usage, and online safety.',
                'event_type': 'training',
                'start_date': timezone.now() + timedelta(days=21),
                'end_date': timezone.now() + timedelta(days=21, hours=3),
                'location': 'Public Library, Main Branch',
                'volunteers_needed': 20,
                'max_volunteers': 25,
            },
        ]

        for event_data in events_data:
            event, created = VolunteerEvent.objects.get_or_create(
                title=event_data['title'],
                defaults={
                    **event_data,
                    'organizer': admin_user,
                    'registration_deadline': event_data['start_date'] - timedelta(days=1),
                }
            )
            if created:
                self.stdout.write(f'Created event: {event.title}')

        # Create sample resources
        resources_data = [
            {
                'title': 'Volunteer Handbook',
                'description': 'Complete guide to volunteering with NEXAS NGO, including policies, procedures, code of conduct, and best practices for all volunteer activities.',
                'resource_type': 'handbook',
                'file_url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
                'file_size': '2.4 MB',
                'category': 'Guidelines',
                'is_featured': True,
            },
            {
                'title': 'Safety Protocols & Emergency Procedures',
                'description': 'Comprehensive safety guidelines and emergency procedures for all volunteer activities, field work, and event participation.',
                'resource_type': 'policy',
                'file_url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
                'file_size': '1.1 MB',
                'category': 'Safety',
                'is_featured': True,
            },
            {
                'title': 'Fundraising Guide & Toolkit',
                'description': 'Effective strategies, templates, and resources for organizing successful fundraising campaigns for NEXAS initiatives.',
                'resource_type': 'toolkit',
                'file_url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
                'file_size': '3.2 MB',
                'category': 'Fundraising',
                'is_featured': True,
            },
            {
                'title': 'Community Engagement Toolkit',
                'description': 'Practical tools and techniques for effective community outreach and engagement in diverse environments.',
                'resource_type': 'toolkit',
                'file_url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
                'file_size': '4.7 MB',
                'category': 'Community Outreach',
                'is_featured': False,
            },
        ]

        for resource_data in resources_data:
            resource, created = VolunteerResource.objects.get_or_create(
                title=resource_data['title'],
                defaults={
                    **resource_data,
                    'last_updated': timezone.now(),
                    'created_by': admin_user,
                }
            )
            if created:
                self.stdout.write(f'Created resource: {resource.title}')

        # Create sample activities
        activities_data = [
            {
                'activity_type': 'hours_logged',
                'title': 'Community outreach work',
                'description': 'Helped distribute food packages to families in need',
                'hours_logged': 4.5,
                'activity_date': timezone.now() - timedelta(days=2),
            },
            {
                'activity_type': 'task_completed',
                'title': 'Completed inventory management',
                'description': 'Organized and catalogued donation items',
                'hours_logged': 3.0,
                'activity_date': timezone.now() - timedelta(days=5),
            },
            {
                'activity_type': 'training_attended',
                'title': 'Attended volunteer orientation',
                'description': 'Completed mandatory training for new volunteers',
                'hours_logged': 2.0,
                'activity_date': timezone.now() - timedelta(days=10),
            },
        ]

        for activity_data in activities_data:
            activity, created = VolunteerActivity.objects.get_or_create(
                volunteer=volunteer_user,
                title=activity_data['title'],
                defaults=activity_data
            )
            if created:
                self.stdout.write(f'Created activity: {activity.title}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Volunteer login: {volunteer_user.email} / volunteer123')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Admin login: {admin_user.email} / admin123')
        )
