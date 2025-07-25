"""
Management command to create a superuser with predefined credentials.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with predefined credentials for NEXAS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@nexas.com',
            help='Admin email address'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Admin@123',
            help='Admin password'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Admin',
            help='Admin first name'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='User',
            help='Admin last name'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email {email} already exists.')
            )
            return

        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=User.UserRole.ADMIN
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created superuser: {user.email}\n'
                f'Email: {email}\n'
                f'Password: {password}\n'
                f'Role: {user.get_role_display()}'
            )
        )
