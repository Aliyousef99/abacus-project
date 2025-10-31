from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class AuditLog(models.Model):
    """An immutable log of significant actions taken by users."""
    
    # Who performed the action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    
    # What was their role at the time? Stored as a string to prevent issues if roles change.
    role = models.CharField(max_length=20)

    # What did they do?
    action = models.CharField(max_length=255) # e.g., "Updated status of agent 'Spectre' to COMPROMISED."

    # When did they do it?
    timestamp = models.DateTimeField(auto_now_add=True)

    # (Optional but Recommended) Generic relation to the object that was affected.
    # This allows you to link an audit entry directly to, for example, the specific Agent object that was modified.
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # (Optional) For storing extra context, like the requested asset in an approval flow.
    details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp'] # Show newest entries first

    def __str__(self):
        return f'[{self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}] [{self.role}] {self.action}'
