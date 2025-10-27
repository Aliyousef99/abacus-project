from django.db import models

class CodexEntry(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    entry_type = models.CharField(max_length=50, default='Historical') # e.g., Historical, Philosophical
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Codex entries"

    def __str__(self):
        return self.title