from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from users.models import UserProfile


class Command(BaseCommand):
    help = "Ensures an HQ superuser exists with role=HQ. Creates or updates credentials."

    def add_arguments(self, parser):
        parser.add_argument('--username', default=getattr(settings, 'HQ_USERNAME', 'hq'))
        parser.add_argument('--password', default=getattr(settings, 'HQ_PASSWORD', None))
        parser.add_argument('--email', default=getattr(settings, 'HQ_EMAIL', 'hq@example.com'))

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if not password:
            # Fall back to a simple default only in dev; print warning
            password = 'ChangeMeNow!123'
            self.stdout.write(self.style.WARNING('HQ_PASSWORD not provided; using default dev password.'))

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.is_staff = True
        user.is_superuser = True
        if password:
            user.set_password(password)
        user.save()

        # Ensure profile exists and set role to HQ
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'HQ'
        profile.save(update_fields=['role'])

        if created:
            self.stdout.write(self.style.SUCCESS(f'HQ user created: {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'HQ user ensured/updated: {username}'))
