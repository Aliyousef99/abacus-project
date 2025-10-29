from django.core.management.base import BaseCommand
from users.models import Mantle
from django.utils import timezone

class Command(BaseCommand):
    help = "Marks expired Protector's Mantles as inactive"

    def handle(self, *args, **options):
        now = timezone.now()
        expired_active = Mantle.objects.filter(is_active=True, end_time__lt=now)
        count = expired_active.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'Successfully marked {count} expired mantles as inactive.'))
