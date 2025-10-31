from django.db import models
from django.contrib.auth.models import User
from lineage.models import Agent as LineageAgent

class CodexEntry(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    content = models.TextField()
    entry_type = models.CharField(max_length=50, default='Historical') # e.g., Historical, Philosophical
    image_urls = models.TextField(blank=True, help_text='Comma-separated image URLs for gallery')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Codex entries"

    def __str__(self):
        return self.title

class Echo(models.Model):
    class Target(models.TextChoices):
        LINEAGE = 'LINEAGE', 'Lineage'
        SCALES = 'SCALES', 'Scales'
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'New'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        ACTIONED = 'ACTIONED', 'Actioned'
        DISMISSED = 'DISMISSED', 'Dismissed'
        PROMOTED = 'PROMOTED', 'Promoted'
    class Confidence(models.TextChoices):
        DIRECT = 'DIRECT', 'Direct Observation'
        VERIFIED = 'VERIFIED', 'Verified Informant'
        CORROBORATED = 'CORROBORATED', 'Corroborated Rumor'
        UNVERIFIED = 'UNVERIFIED', 'Unverified Tip'

    title = models.CharField(max_length=255)
    content = models.TextField()
    suggested_target = models.CharField(max_length=20, choices=Target.choices, default=Target.LINEAGE)
    confidence = models.CharField(max_length=20, choices=Confidence.choices, default=Confidence.UNVERIFIED)
    involved_entities = models.JSONField(null=True, blank=True)
    evidence_urls = models.TextField(blank=True, help_text='Comma-separated list of URLs for evidence')
    assigned_agents = models.ManyToManyField(LineageAgent, related_name='assigned_reports', blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='echoes_created')
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='echoes_decided')
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Echo: {self.title} ({self.status})"

class Task(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUCCESS = 'SUCCESS', 'Success'
        FAILURE = 'FAILURE', 'Failure'
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks_created')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks_assigned')
    created_at = models.DateTimeField(auto_now_add=True)
    related_app = models.CharField(max_length=20, blank=True)
    related_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Task: {self.title} [{self.status}]"

class SiloComment(models.Model):
    echo = models.ForeignKey(Echo, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class VaultItem(models.Model):
    class ItemType(models.TextChoices):
        SHELL_CORP = 'SHELL_CORP', 'Shell Corporation'
        BANK_ACCOUNT = 'BANK_ACCOUNT', 'Untraceable Bank Account'
        CRYPTO_WALLET = 'CRYPTO_WALLET', 'Cryptocurrency Wallet'
        KEYPASS = 'KEYPASS', 'Key Passphrase'

    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    name = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    secret = models.TextField(blank=True, help_text='Encrypted or protected secret payload')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_item_type_display()}: {self.name}"

class PropertyDossier(models.Model):
    """Physical locations: safehouses, warehouses, fronts."""
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    photos_urls = models.TextField(blank=True, help_text='Comma-separated list of photo URLs')
    blueprints_urls = models.TextField(blank=True, help_text='Comma-separated blueprint URLs')
    security_details = models.TextField(blank=True)
    vulnerabilities = models.TextField(blank=True)
    stored_items = models.ManyToManyField(VaultItem, related_name='properties', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Property: {self.name}"

from lineage.models import Agent as LineageAgent

class Vehicle(models.Model):
    """Fleet management entries."""
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(null=True, blank=True)
    vin = models.CharField(max_length=100, blank=True)
    license_plate_clean = models.CharField(max_length=50, blank=True)
    license_plate_cloned = models.CharField(max_length=50, blank=True)
    modifications = models.TextField(blank=True, help_text='Armor, compartments, etc.')
    last_known_location = models.CharField(max_length=255, blank=True)
    picture_urls = models.TextField(blank=True, help_text='Comma-separated URLs')
    assigned_agent = models.ForeignKey(LineageAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vehicles')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vehicle: {self.make} {self.model} ({self.license_plate_clean or 'N/A'})"

# --- Codex Category Configuration ---
class CodexCategoryConfig(models.Model):
    """Optional per-category widget configuration (cover image, description)."""
    name = models.CharField(max_length=100, unique=True)
    image_url = models.TextField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"CodexCategoryConfig({self.name})"

# --- Secure Communications & Notifications ---

class Bulletin(models.Model):
    """System bulletin posted by the Protector for specific audience roles."""
    class Audience(models.TextChoices):
        HEIR = 'HEIR', 'Heir'
        OVERLOOKER = 'OVERLOOKER', 'Overlooker'
        ALL = 'ALL', 'All'

    title = models.CharField(max_length=255)
    message = models.TextField()
    audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.ALL)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bulletins_posted')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bulletin: {self.title} → {self.audience}"

class BulletinAck(models.Model):
    bulletin = models.ForeignKey(Bulletin, on_delete=models.CASCADE, related_name='acks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulletin_acks')
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('bulletin', 'user')

class Notification(models.Model):
    """Discrete notifications for users about critical events."""
    class Type(models.TextChoices):
        SILO_REPORT = 'SILO_REPORT', 'New Silo Report'
        TASK_ASSIGNED = 'TASK_ASSIGNED', 'Task Assigned'
        OPERATION_STATUS = 'OPERATION_STATUS', 'Operation Status Changed'
        MANTLE = 'MANTLE', "Protector's Mantle"
        BULLETIN_ACK = 'BULLETIN_ACK', 'Bulletin Acknowledged'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=40, choices=Type.choices)
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    @property
    def is_read(self):
        return self.read_at is not None
