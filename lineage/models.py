from django.db import models

class Agent(models.Model):
    alias = models.CharField(max_length=100, unique=True)
    real_name = models.CharField(max_length=255, help_text="CLASSIFIED")
    status = models.CharField(max_length=50, default='Active') # e.g., Active, Inactive, Compromised, Retired
    loyalty_type = models.CharField(max_length=50) # e.g., Ideological, Financial, Coerced
    key_skill = models.CharField(max_length=100) # e.g., Infiltration, Wetwork, Tech
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.alias