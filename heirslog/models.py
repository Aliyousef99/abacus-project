from django.db import models
from django.conf import settings

class HeirsLogEntry(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entry_date = models.DateField()
    title = models.CharField(max_length=255, blank=True, default='')
    # Make sections optional/blank-allowed
    situational_overview = models.TextField(blank=True)
    critical_intelligence = models.TextField(blank=True)
    operational_status = models.TextField(blank=True)
    strategic_analysis = models.TextField(blank=True)
    proposed_actions = models.TextField(blank=True)
    # Persisted presentation preferences for the combined notes
    notes_font_family = models.CharField(max_length=255, blank=True)
    notes_font_size = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Log Entry for {self.entry_date} by {self.author.username}"

class HeirsLogComment(models.Model):
    entry = models.ForeignKey(HeirsLogEntry, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.entry.entry_date}"
