from django.db import models

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Agent(models.Model):
    """ Represents an external agent or contact within The Scales. """
    name = models.CharField(max_length=255, blank=True, help_text="The agent's real name, if known.")
    alias = models.CharField(max_length=100, unique=True, blank=True)
    rank = models.CharField(max_length=100, blank=True)
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    known_locations = models.TextField(blank=True)
    known_vehicles = models.TextField(blank=True)
    picture_url = models.URLField(max_length=500, blank=True, null=True)
    surveillance_images = models.TextField(blank=True, help_text="Comma-separated URLs of surveillance images.")
    threat_level = models.PositiveIntegerField(default=50, blank=True, null=True, help_text="A score from 0-100 indicating threat level.")
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.alias

class Faction(models.Model):
    name = models.CharField(max_length=150, unique=True)
    threat_index = models.PositiveIntegerField(default=50, help_text="A score from 0-100")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    picture_url = models.URLField(max_length=500, blank=True, null=True)
    allies = models.CharField(max_length=255, blank=True, help_text="Comma-separated list of allied factions")
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    members = models.ManyToManyField(Agent, related_name='factions', blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.members.count()

class Leverage(models.Model):
    faction = models.ForeignKey(Faction, related_name='leverage_points', on_delete=models.CASCADE)
    description = models.TextField(help_text="Details of the compromising information.")
    potency = models.CharField(max_length=50, default='High') # e.g., Low, Medium, High, Critical
    acquired_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"Leverage on {self.faction.name}"

from django.contrib.auth.models import User

class FactionHistory(models.Model):
    """Historical snapshots for a faction's key indicators."""
    faction = models.ForeignKey(Faction, related_name='history', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    threat_index = models.IntegerField(null=True, blank=True)
    member_count = models.IntegerField(null=True, blank=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.faction.name} @ {self.timestamp:%Y-%m-%d %H:%M}"

from lineage.models import Agent as LineageAgent

class Connection(models.Model):
    class Relationship(models.TextChoices):
        INFORMANT = 'INFORMANT', 'Informant'
        LEVERAGE = 'LEVERAGE', 'Leverage (Blackmail)'
        FAMILY_TIE = 'FAMILY_TIE', 'Family Tie'
        PAST_AFFILIATION = 'PAST_AFFILIATION', 'Past Affiliation'
        RIVAL = 'RIVAL', 'Rival'
        HANDLER = 'HANDLER', 'Handler'

    scales_agent = models.ForeignKey(Agent, related_name='connections', on_delete=models.CASCADE)
    lineage_agent = models.ForeignKey(LineageAgent, related_name='external_connections', on_delete=models.CASCADE)
    relationship = models.CharField(max_length=32, choices=Relationship.choices)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('scales_agent', 'lineage_agent')

    def __str__(self):
        return f"{self.scales_agent.alias} ↔ {self.lineage_agent.alias} ({self.get_relationship_display()})"
