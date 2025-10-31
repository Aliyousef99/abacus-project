from django.db import models


class IndexProfile(models.Model):
    class Classification(models.TextChoices):
        ASSET_TALON = 'ASSET_TALON', 'Asset (Talon)'
        CRIMINAL_AFFILIATED = 'CRIMINAL_AFFILIATED', 'Criminal (Affiliated)'
        CRIMINAL_UNAFFILIATED = 'CRIMINAL_UNAFFILIATED', 'Criminal (Unaffiliated)'
        LAW_ENFORCEMENT = 'LAW_ENFORCEMENT', 'Law Enforcement'
        GOVERNMENT_DOJ = 'GOVERNMENT_DOJ', 'Government / DOJ'
        CIVILIAN_HIGH = 'CIVILIAN_HIGH', 'Civilian (High Value)'
        CIVILIAN_LOW = 'CIVILIAN_LOW', 'Civilian (Low Value)'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        DECEASED = 'DECEASED', 'Deceased'
        INCARCERATED = 'INCARCERATED', 'Incarcerated'
        MISSING = 'MISSING', 'Missing'

    class ThreatLevel(models.TextChoices):
        NONE = 'NONE', 'None'
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    full_name = models.CharField(max_length=255)
    aliases = models.TextField(blank=True)
    classification = models.CharField(max_length=32, choices=Classification.choices, blank=True, null=True)
    # Link to one or more Scales Factions (can be empty)
    affiliations = models.ManyToManyField('scales.Faction', through='IndexAffiliation', related_name='index_profiles', blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, blank=True, null=True)
    threat_level = models.CharField(max_length=16, choices=ThreatLevel.choices, default=ThreatLevel.NONE, blank=True, null=True)

    biography = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    known_locations = models.TextField(blank=True)
    known_vehicles = models.TextField(blank=True)

    # Keep this as URL list for now to avoid adding storage; can be moved to file uploads later
    surveillance_urls = models.TextField(blank=True, help_text='Comma-separated URLs of surveillance media')
    picture_url = models.URLField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class IndexAffiliation(models.Model):
    profile = models.ForeignKey(IndexProfile, on_delete=models.CASCADE, related_name='affiliation_links')
    faction = models.ForeignKey('scales.Faction', on_delete=models.CASCADE, related_name='affiliation_links')
    level = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('profile', 'faction')

    def __str__(self):
        return f"{self.profile.full_name} ↔ {getattr(self.faction, 'name', self.faction_id)} ({self.level or '-'})"
