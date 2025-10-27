from django.db import models

class Faction(models.Model):
    name = models.CharField(max_length=150, unique=True)
    threat_index = models.PositiveIntegerField(default=50, help_text="A score from 0-100")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Leverage(models.Model):
    faction = models.ForeignKey(Faction, related_name='leverage_points', on_delete=models.CASCADE)
    description = models.TextField(help_text="Details of the compromising information.")
    potency = models.CharField(max_length=50, default='High') # e.g., Low, Medium, High, Critical
    acquired_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Leverage on {self.faction.name}"