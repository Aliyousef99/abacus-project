from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    class Role(models.TextChoices):
        PROTECTOR = 'PROTECTOR', 'Protector'
        HEIR = 'HEIR', 'Heir'
        OBSERVER = 'OBSERVER', 'Observer'
        HQ = 'HQ', 'Headquarters'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Public-facing name shown to other users; keeps username private
    display_name = models.CharField(max_length=150, blank=True, default='')
    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.OBSERVER
    )

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'

class Mantle(models.Model):
    """Represents the temporary delegation of Protector authority."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mantle')
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_mantles')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_currently_active(self):
        """Check if the mantle is currently active."""
        return self.is_active and self.end_time > timezone.now()

    def __str__(self):
        status = "Active" if self.is_currently_active() else "Expired"
        return f"Mantle for {self.user.username} until {self.end_time} ({status})"

class SiteState(models.Model):
    """Singleton-like state record to control global site availability."""
    is_shutdown = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SiteState(shutdown={self.is_shutdown})"

    @classmethod
    def get_state(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class PanicAlert(models.Model):
    """Records panic alerts initiated by users with a message/reason."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='panic_resolved')

    @property
    def is_resolved(self):
        return self.resolved_at is not None

# Signal to create a UserProfile automatically when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Default display_name to first + last or fallback to username
        base_name = (f"{(instance.first_name or '').strip()} {(instance.last_name or '').strip()}").strip()
        if not base_name:
            base_name = instance.username
        UserProfile.objects.create(user=instance, display_name=base_name)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
