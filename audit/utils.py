from django.db import models
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
from users.models import Mantle
from django.utils import timezone

def log_action(user, action: str, target: models.Model = None, details: dict = None):
    """
    A centralized utility for creating audit log entries.

    :param user: The user performing the action.
    :param action: A string describing the action (e.g., 'Created agent Spectre').
    :param target: The model instance being acted upon (optional).
    :param details: A dictionary for storing extra context (optional).
    """
    try:
        # Determine effective role, considering active Mantle
        role = user.profile.role
        if role == 'HEIR':
            try:
                mantle = user.mantle
                if mantle and mantle.is_currently_active():
                    role = "PROTECTOR (Acting Heir)"
            except Mantle.DoesNotExist:
                pass
    except AttributeError:
        role = 'ANONYMOUS'  # Should not happen for authenticated users

    AuditLog.objects.create(
        user=user,
        role=role,
        action=action,
        content_object=target,
        details=details
    )
